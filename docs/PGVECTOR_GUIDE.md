# pgvector — Index and Distance Guide

Reference for configuring pgvector indexes in the context of RAG with Mistral embeddings.

---

## Distance operators

pgvector exposes three distance operators and their corresponding index operator classes.

| Operator | `postgresql_ops` | Measures | Range |
|----------|-----------------|----------|-------|
| `<=>` | `vector_cosine_ops` | Cosine distance | [0, 2] |
| `<->` | `vector_l2_ops` | Euclidean (L2) distance | [0, ∞) |
| `<#>` | `vector_ip_ops` | Negative inner product | (−∞, 0] |

### Cosine distance

Measures the **angle** between two vectors, ignoring their magnitude.

```
cosine_distance(a, b) = 1 - (a · b) / (‖a‖ × ‖b‖)
```

- 0 → identical direction (same semantic meaning)
- 1 → orthogonal (no relation)
- 2 → opposite directions

The magnitude of each vector does not affect the result. Two embeddings with
the same semantic meaning but different scales will still score 0.

### L2 distance

Measures the **straight-line distance** between two points in vector space.

```
l2_distance(a, b) = √Σ(aᵢ − bᵢ)²
```

Sensitive to magnitude. Two vectors pointing in the same direction but with
different norms will appear far apart.

### Comparison

```
vec_A = [0.5, 0.5]   # "refund policy"
vec_B = [1.0, 1.0]   # same meaning, 2× larger norm

cosine(A, B) = 0.0   → semantically identical ✅
L2(A, B)     = 0.71  → appear different        ❌
```

### Which to use with `mistral-embed`

Mistral embeddings are **not unit-normalized** — their magnitude varies across
documents. This makes cosine distance the correct choice: it captures semantic
similarity independently of embedding scale.

> Use `vector_cosine_ops` (`<=>`) with `mistral-embed`.

If embeddings were guaranteed to be unit vectors (‖v‖ = 1 for all v), cosine
and L2 would be mathematically equivalent and either could be used. Mistral
does not guarantee this.

---

## Index types

pgvector supports two approximate nearest neighbor (ANN) index types.

### HNSW — Hierarchical Navigable Small World

```sql
CREATE INDEX ON document_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```

Builds a **multi-layer graph**. Each vector is connected to its `m` nearest
neighbors at each level. A query starts at the top (coarse) layer and
navigates down to the bottom (fine) layer to find the closest vectors.

**Construction parameters:**

| Parameter | Default | Effect |
|-----------|---------|--------|
| `m` | 16 | Connections per node per layer. Higher → better recall, more RAM, slower build. |
| `ef_construction` | 64 | Candidate list size during build. Higher → more accurate index, slower build. |

**Query parameter** (set at query time, not index creation):

```sql
SET hnsw.ef_search = 40;  -- default: 40
```

Higher `ef_search` → better recall, slower queries.

### IVFFlat — Inverted File with Flat compression

```sql
CREATE INDEX ON document_chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

Divides the vector space into `lists` clusters (Voronoi cells) computed from
existing data. A query searches only the nearest `probes` clusters instead of
all vectors.

**Requires data at index creation time** — the cluster centroids are computed
from the rows already in the table. An index built on an empty table is
useless.

**Query parameter:**

```sql
SET ivfflat.probes = 1;  -- default: 1
```

Higher `probes` → better recall, slower queries.

### Comparison

| | **HNSW** | **IVFFlat** |
|---|---|---|
| Query speed | ⚡ Faster | Fast |
| Recall | Higher | Good |
| Build speed | Slower | Faster |
| RAM usage | Higher | Lower |
| Works on empty table | ✅ Yes | ❌ No |
| Incremental inserts | ✅ Efficient | ⚠ Degrades over time |

### Which to use with `mistral-embed`

HNSW is the better choice for a RAG pipeline because:

1. **Alembic migrations run on empty tables.** IVFFlat cannot compute cluster
   centroids without existing rows; an index created during migration would be
   empty and ineffective.
2. **Documents are ingested incrementally.** HNSW updates its graph on each
   `INSERT`. IVFFlat's cluster assignments become stale as new data is added
   (requiring periodic `REINDEX`).
3. **Recall is higher** for HNSW at equivalent query latency.

> Use `USING hnsw` for this project.

---

## Tuning recommendations

The values currently in use (`m = 16`, `ef_construction = 64`) are the pgvector
defaults and a reasonable starting point. Adjust if retrieval quality needs
improvement.

| Scenario | Adjustment |
|----------|------------|
| Low recall (wrong chunks returned) | Increase `ef_search` (query time) |
| Persistent low recall | Rebuild index with higher `m` (32) and `ef_construction` (128) |
| High RAM pressure | Lower `m` to 8 |
| Slow queries | Lower `ef_search` |

To change `ef_search` per session:

```python
# In pgvector_retriever.py, before executing the similarity query
await db.execute(text("SET hnsw.ef_search = 80"))
```

---

## Current configuration (this project)

```python
# data/alembic/versions/6a6d4579355d_fix_uuid_types.py
postgresql_using='hnsw'
postgresql_ops={'embedding': 'vector_cosine_ops'}
postgresql_with={'m': '16', 'ef_construction': '64'}
```

```sql
-- Equivalent SQL
CREATE INDEX document_chunks_embedding_idx
  ON document_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```

**Summary:** HNSW + cosine distance is the correct combination for incremental
RAG ingestion with Mistral embeddings.

---

*Last updated: 2026-04-08*
