# Project Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the project in two steps: (1) consolidate DB-related files under `data/`, (2) group all RAG engine modules under `src/rag/rag/`.

**Architecture:** Currently `alembic/` and `db/` are loose at the root; they move into `data/`. The four RAG modules (`agent/`, `embeddings/`, `ingestion/`, `retriever/`) are flat siblings of `api/`; they move into a `rag/` sub-package to make the API / RAG split explicit. The `db/`, `config/`, `observability/`, and `evaluation/` modules do not move.

**Tech Stack:** Python, uv, Alembic, Docker Compose, pytest.

---

## File Map

### Task 1 — Data directory consolidation

| Action | From | To |
|--------|------|----|
| Move dir | `alembic/` | `data/alembic/` |
| Move dir | `db/` | `data/db/` |
| Modify | `alembic.ini` line 8 | `script_location = %(here)s/data/alembic` |
| Modify | `docker-compose.yml` line 14 | `./data/db/init/init.sql:...` |

### Task 2 — Create `rag/` package

| Action | Path |
|--------|------|
| Create | `src/rag/rag/__init__.py` |
| Move dir | `src/rag/agent/` → `src/rag/rag/agent/` |
| Move dir | `src/rag/embeddings/` → `src/rag/rag/embeddings/` |
| Move dir | `src/rag/ingestion/` → `src/rag/rag/ingestion/` |
| Move dir | `src/rag/retriever/` → `src/rag/rag/retriever/` |

### Task 3 — Update internal imports (inside moved modules)

| File | Old import | New import |
|------|-----------|-----------|
| `rag/agent/nodes.py` | `rag.agent.prompts` | `rag.rag.agent.prompts` |
| `rag/agent/nodes.py` | `rag.agent.state` | `rag.rag.agent.state` |
| `rag/agent/nodes.py` | `rag.retriever` | `rag.rag.retriever` |
| `rag/agent/graph.py` | `rag.agent.nodes` | `rag.rag.agent.nodes` |
| `rag/agent/graph.py` | `rag.agent.state` | `rag.rag.agent.state` |
| `rag/ingestion/pipeline.py` | `rag.embeddings` | `rag.rag.embeddings` |
| `rag/ingestion/pipeline.py` | `rag.ingestion.chunker` | `rag.rag.ingestion.chunker` |
| `rag/ingestion/pipeline.py` | `rag.ingestion.pdf_loader` | `rag.rag.ingestion.pdf_loader` |
| `rag/retriever/pgvector_retriever.py` | `rag.embeddings` | `rag.rag.embeddings` |

### Task 4 — Update external imports (consumers outside `rag/`)

| File | Old import | New import |
|------|-----------|-----------|
| `api/routers/chat.py` | `rag.agent.graph` | `rag.rag.agent.graph` |
| `api/routers/ingestion.py` | `rag.ingestion.pipeline` | `rag.rag.ingestion.pipeline` |
| `evaluation/ragas_pipeline.py` | `rag.agent.graph` | `rag.rag.agent.graph` |
| `tests/unit/test_chunker.py` | `rag.ingestion.chunker` | `rag.rag.ingestion.chunker` |
| `tests/unit/test_chunker.py` | `patch("rag.ingestion.chunker.get_settings")` | `patch("rag.rag.ingestion.chunker.get_settings")` |
| `tests/unit/test_ingestion_pipeline.py` | `rag.ingestion.pipeline` | `rag.rag.ingestion.pipeline` |
| `tests/unit/test_ingestion_pipeline.py` | `patch("rag.ingestion.pipeline.load_pdf")` | `patch("rag.rag.ingestion.pipeline.load_pdf")` |

### Task 5 — Update documentation

| File | What changes |
|------|-------------|
| `docs/PROJECT_STRUCTURE.md` | Directory tree + descriptions |
| `docs/AGENTS.md` | File Summaries section |
| `docs/TECHNICAL_GUIDE.md` | Migrations path note |

---

## Task 1: Consolidate data directory

**Files:**
- Move: `alembic/` → `data/alembic/`
- Move: `db/` → `data/db/`
- Modify: `alembic.ini`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Confirm tests pass before touching anything**

```bash
uv run pytest --tb=short -q
```

Expected: all tests pass (or same failures as before — record baseline).

- [ ] **Step 2: Move directories**

```bash
mkdir -p data
mv alembic data/alembic
mv db data/db
```

- [ ] **Step 3: Update `alembic.ini`**

Change line 8:

```ini
script_location = %(here)s/data/alembic
```

- [ ] **Step 4: Update `docker-compose.yml`**

Change the volumes line:

```yaml
- ./data/db/init/init.sql:/docker-entrypoint-initdb.d/init.sql
```

- [ ] **Step 5: Verify Alembic can still find the migrations**

```bash
uv run alembic history
```

Expected: lists the three migration revisions without error.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: move alembic/ and db/ under data/"
```

---

## Task 2: Create `rag/` package and move modules

**Files:**
- Create: `src/rag/rag/__init__.py`
- Move: `src/rag/agent/` → `src/rag/rag/agent/`
- Move: `src/rag/embeddings/` → `src/rag/rag/embeddings/`
- Move: `src/rag/ingestion/` → `src/rag/rag/ingestion/`
- Move: `src/rag/retriever/` → `src/rag/rag/retriever/`

- [ ] **Step 1: Create the `rag/` package and move the four modules**

```bash
mkdir src/rag/rag
touch src/rag/rag/__init__.py
mv src/rag/agent      src/rag/rag/agent
mv src/rag/embeddings src/rag/rag/embeddings
mv src/rag/ingestion  src/rag/rag/ingestion
mv src/rag/retriever  src/rag/rag/retriever
```

- [ ] **Step 2: Confirm the directories exist**

```bash
ls src/rag/rag/
```

Expected: `__init__.py  agent/  embeddings/  ingestion/  retriever/`

---

## Task 3: Update internal imports in the moved modules

**Files:**
- Modify: `src/rag/rag/agent/nodes.py`
- Modify: `src/rag/rag/agent/graph.py`
- Modify: `src/rag/rag/ingestion/pipeline.py`
- Modify: `src/rag/rag/retriever/pgvector_retriever.py`

- [ ] **Step 1: Fix `rag/agent/nodes.py`**

Replace these three imports:

```python
# Before
from rag.agent.prompts import RAG_PROMPT, ROUTE_PROMPT, SYSTEM_PROMPT
from rag.agent.state import AgentState
from rag.retriever import pgvector_retriever

# After
from rag.rag.agent.prompts import RAG_PROMPT, ROUTE_PROMPT, SYSTEM_PROMPT
from rag.rag.agent.state import AgentState
from rag.rag.retriever import pgvector_retriever
```

- [ ] **Step 2: Fix `rag/agent/graph.py`**

```python
# Before
from rag.agent.nodes import generate, load_history, retrieve, route, save_turn
from rag.agent.state import AgentState

# After
from rag.rag.agent.nodes import generate, load_history, retrieve, route, save_turn
from rag.rag.agent.state import AgentState
```

- [ ] **Step 3: Fix `rag/ingestion/pipeline.py`**

```python
# Before
from rag.embeddings import mistral_embeddings
from rag.ingestion.chunker import chunk_texts
from rag.ingestion.pdf_loader import load_pdf

# After
from rag.rag.embeddings import mistral_embeddings
from rag.rag.ingestion.chunker import chunk_texts
from rag.rag.ingestion.pdf_loader import load_pdf
```

- [ ] **Step 4: Fix `rag/retriever/pgvector_retriever.py`**

```python
# Before
from rag.embeddings import mistral_embeddings

# After
from rag.rag.embeddings import mistral_embeddings
```

---

## Task 4: Update external imports (consumers outside `rag/`)

**Files:**
- Modify: `src/rag/api/routers/chat.py`
- Modify: `src/rag/api/routers/ingestion.py`
- Modify: `src/rag/evaluation/ragas_pipeline.py`
- Modify: `tests/unit/test_chunker.py`
- Modify: `tests/unit/test_ingestion_pipeline.py`

- [ ] **Step 1: Fix `api/routers/chat.py`**

```python
# Before
from rag.agent.graph import build_graph

# After
from rag.rag.agent.graph import build_graph
```

- [ ] **Step 2: Fix `api/routers/ingestion.py`**

```python
# Before
from rag.ingestion.pipeline import ingest_pdf

# After
from rag.rag.ingestion.pipeline import ingest_pdf
```

- [ ] **Step 3: Fix `evaluation/ragas_pipeline.py`**

```python
# Before
from rag.agent.graph import build_graph

# After
from rag.rag.agent.graph import build_graph
```

The lazy import inside the function (`from rag.db.models.conversation import Conversation`) does not change.

- [ ] **Step 4: Fix `tests/unit/test_chunker.py`**

```python
# Before
from rag.ingestion.chunker import chunk_texts
...
with patch("rag.ingestion.chunker.get_settings") as mock_settings:
...  # (three occurrences of this patch path)

# After
from rag.rag.ingestion.chunker import chunk_texts
...
with patch("rag.rag.ingestion.chunker.get_settings") as mock_settings:
```

There are three `patch` calls to update (one per test function).

- [ ] **Step 5: Fix `tests/unit/test_ingestion_pipeline.py`**

```python
# Before
from rag.ingestion.pipeline import _compute_hash, ingest_pdf
...
with patch("rag.ingestion.pipeline.load_pdf", ...):

# After
from rag.rag.ingestion.pipeline import _compute_hash, ingest_pdf
...
with patch("rag.rag.ingestion.pipeline.load_pdf", ...):
```

- [ ] **Step 6: Run tests — all must pass**

```bash
uv run pytest --tb=short -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor: group agent/embeddings/ingestion/retriever under rag/"
```

---

## Task 5: Update documentation

**Files:**
- Modify: `docs/PROJECT_STRUCTURE.md`
- Modify: `docs/AGENTS.md`
- Modify: `docs/TECHNICAL_GUIDE.md`

- [ ] **Step 1: Update `docs/PROJECT_STRUCTURE.md`**

Replace the full directory tree with:

```text
simplon-rag-sample/
├── src/rag/                # Application source package
│   ├── config/
│   │   └── settings.py         # Pydantic BaseSettings (all env vars)
│   ├── db/
│   │   ├── base.py             # SQLAlchemy DeclarativeBase
│   │   ├── session.py          # Async engine + get_db()
│   │   └── models/
│   │       ├── document.py     # Document + DocumentChunk ORM models
│   │       └── conversation.py # Conversation + Message ORM models
│   ├── rag/                    # RAG engine (pure domain logic)
│   │   ├── agent/
│   │   │   ├── state.py        # AgentState TypedDict
│   │   │   ├── prompts.py      # SYSTEM_PROMPT, ROUTE_PROMPT, RAG_PROMPT
│   │   │   ├── nodes.py        # LangGraph node functions (async)
│   │   │   └── graph.py        # build_graph() → CompiledGraph
│   │   ├── embeddings/
│   │   │   └── mistral_embeddings.py # Wrapper MistralAIEmbeddings
│   │   ├── ingestion/
│   │   │   ├── pdf_loader.py   # pypdf → list[str] per page
│   │   │   ├── chunker.py      # RecursiveCharacterTextSplitter
│   │   │   └── pipeline.py     # SHA-256 dedup → load → chunk → embed → store
│   │   └── retriever/
│   │       └── pgvector_retriever.py # Cosine similarity search via <=>
│   ├── api/
│   │   ├── app.py              # create_app() FastAPI factory
│   │   └── routers/
│   │       ├── health.py       # GET /api/v1/health
│   │       ├── ingestion.py    # POST/GET/DELETE /api/v1/documents
│   │       ├── chat.py         # POST/GET /api/v1/conversations
│   │       └── eval.py         # POST /api/v1/eval/run
│   ├── observability/
│   │   └── langfuse_handler.py # Langfuse v4 callback + client helpers
│   └── evaluation/
│       └── ragas_pipeline.py   # Ragas evaluation runner
├── data/
│   ├── alembic/                # DB migrations
│   │   ├── env.py              # Async Alembic env
│   │   └── versions/
│   │       ├── 0001_documents.py
│   │       ├── 0002_conversations.py
│   │       └── 6a6d4579355d_fix_uuid_types.py
│   └── db/
│       └── init/
│           └── init.sql        # CREATE EXTENSION vector (Docker init)
├── tests/
│   ├── conftest.py             # Fixtures (SQLite in-memory, mock embeddings)
│   ├── unit/
│   │   ├── test_chunker.py
│   │   └── test_ingestion_pipeline.py
│   └── integration/
│       ├── test_api_chat.py
│       └── test_api_ingestion.py
├── .github/                    # GitHub configuration
├── docs/                       # Documentation
├── alembic.ini                 # Alembic configuration (script_location → data/alembic)
├── pyproject.toml
├── uv.lock
├── .python-version
├── main.py
├── .env.example
├── .pre-commit-config.yaml
├── .pymarkdown
├── CLAUDE.md
└── README.md
```

Update the last-updated footer to `2026-04-08`.

- [ ] **Step 2: Update `docs/AGENTS.md` — File Summaries section**

In the `PROJECT_STRUCTURE.md` summary bullet, replace:

```
- Source: `src/rag/` (config, db, ingestion, embeddings, retriever, agent, api, observability, evaluation)
- Migrations: `alembic/versions/` (0001 documents, 0002 conversations)
```

With:

```
- Source: `src/rag/` (config, db, api, observability, evaluation) + `src/rag/rag/` (agent, embeddings, ingestion, retriever)
- Migrations: `data/alembic/versions/`
- DB init scripts: `data/db/init/init.sql`
- `rag_eval/`: RAG evaluation playground (do not modify)
```

Update the last-updated footer to `2026-04-08`.

- [ ] **Step 3: Update `docs/TECHNICAL_GUIDE.md` — Alembic section**

No path changes needed in the commands themselves (`alembic upgrade head` etc. still work via `alembic.ini`). Just update the last-updated footer to `2026-04-08`.

- [ ] **Step 4: Lint and commit**

```bash
uv run pymarkdownlnt fix --recurse docs/
uv run pymarkdownlnt scan --recurse docs/
git add docs/
git commit -m "docs: update structure docs after data/ and rag/ reorganisation"
```

---

*Plan written 2026-04-08*
