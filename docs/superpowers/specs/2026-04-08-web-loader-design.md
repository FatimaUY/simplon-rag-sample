# Web Loader Design

**Date:** 2026-04-08
**Status:** Approved

## Summary

Add a web loader to the RAG ingestion pipeline that recursively crawls a list of URLs and ingests
their content into the vector store. Crawling stays within the same domain, has no depth limit, and
is bounded by a configurable max-pages setting.

## Architecture

New components mirror the existing PDF ingestion pattern:

```
src/rag/rag/ingestion/
  web_loader.py     ← new: recursive crawl via LangChain RecursiveUrlLoader
  pipeline.py       ← extended: new ingest_url() function

src/rag/api/routers/
  ingestion.py      ← extended: POST /documents/ingest-urls

src/rag/config/
  settings.py       ← extended: WEB_MAX_PAGES setting
```

## Components

### `web_loader.py`

Function signature: `load_url(url: str, max_pages: int) -> tuple[list[str], dict]`

- Uses `RecursiveUrlLoader` from `langchain_community.document_loaders`
- `max_depth=10` (effectively unlimited depth)
- Restricts crawl to the same domain as the starting URL
- Caps at `max_pages` total pages
- Strips HTML tags to extract plain text
- Returns `(texts, metadata)` — same interface as `load_pdf()` so `chunk_texts()` is reused unchanged

### `ingest_url()` in `pipeline.py`

Mirror of `ingest_pdf()`:

- **Deduplication**: SHA-256 hash of the normalized URL stored as `file_hash` — re-ingesting the
  same URL is a no-op
- **Source metadata**: `{"source": url, "type": "web"}` passed to `chunk_texts()`
- Returns the same `IngestionResult` dataclass

### API endpoint

`POST /documents/ingest-urls`

Request body (JSON):

```json
{
  "urls": ["https://example.com", "https://other.com"],
  "max_pages": 100
}
```

- `max_pages` is optional; defaults to `settings.web_max_pages`
- URLs are processed sequentially
- Returns a list of `IngestionResult`-shaped dicts, one per URL
- Each URL result indicates `already_existed` if the URL was previously ingested

### Settings

Add to `Settings`:

```python
WEB_MAX_PAGES: int = 100
```

Readable via environment variable `WEB_MAX_PAGES`.

## Data Flow

```
POST /documents/ingest-urls
  → ingest_url(url, db)
    → load_url(url, max_pages)       # crawl + extract text
    → chunk_texts(pages, metadata)   # reuse existing chunker
    → embed_documents(texts)         # Mistral embed batch
    → persist Document + DocumentChunk rows
```

## Deduplication Strategy

URLs are normalized (stripped of trailing slashes, lowercased scheme+host) before hashing.
The SHA-256 of the normalized URL is stored as `file_hash` on the `Document` row, reusing
the existing unique constraint.

## Error Handling

- Invalid or unreachable URLs raise `ValueError` before any DB writes
- Empty crawl result (no text extracted) raises `ValueError`
- Each URL in a batch is processed independently; one failure does not abort the others

## Dependencies

- `langchain-community` — provides `RecursiveUrlLoader` (already transitively available via
  langchain; confirm with `uv add langchain-community` if not present)
- `beautifulsoup4` — used by `RecursiveUrlLoader` for HTML parsing (add if not present)
