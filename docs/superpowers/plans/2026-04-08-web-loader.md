# Web Loader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a recursive web crawler that ingests a list of URLs into the RAG vector store,
staying within each URL's domain and bounded by a configurable max-pages setting.

**Architecture:** A new `web_loader.py` mirrors `pdf_loader.py` — same return type so `chunk_texts()`
is reused unchanged. A new `ingest_url()` in `pipeline.py` mirrors `ingest_pdf()` with URL-based
deduplication. A new `POST /documents/ingest-urls` endpoint accepts a JSON list of URLs.

**Tech Stack:** Python 3.14, LangChain `RecursiveUrlLoader` (from `langchain-community`),
`beautifulsoup4` for HTML stripping, FastAPI, SQLAlchemy async, Mistral embeddings, pgvector.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `pyproject.toml` | Add `langchain-community` and `beautifulsoup4` deps |
| Modify | `src/rag/config/settings.py` | Add `web_max_pages: int = 100` |
| Create | `src/rag/rag/ingestion/web_loader.py` | Crawl URL, return `(list[str], dict)` |
| Modify | `src/rag/rag/ingestion/pipeline.py` | Add `ingest_url()` + `_hash_url()` |
| Modify | `src/rag/api/routers/ingestion.py` | Add `POST /documents/ingest-urls` |
| Create | `tests/unit/test_web_loader.py` | Unit tests for `web_loader.py` |
| Modify | `tests/unit/test_ingestion_pipeline.py` | Unit tests for `ingest_url()` |
| Modify | `tests/integration/test_api_ingestion.py` | Integration tests for new endpoint |

---

## Task 1: Add dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add dependencies**

```bash
cd /path/to/simplon-rag-sample
uv add langchain-community beautifulsoup4
```

Expected: `pyproject.toml` updated, `uv.lock` regenerated, no errors.

- [ ] **Step 2: Verify install**

```bash
uv run python -c "from langchain_community.document_loaders import RecursiveUrlLoader; print('ok')"
```

Expected output: `ok`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add langchain-community and beautifulsoup4 for web loader"
```

---

## Task 2: Add `web_max_pages` setting

**Files:**
- Modify: `src/rag/config/settings.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_web_loader.py` (create the file):

```python
from unittest.mock import patch

from rag.config.settings import Settings


def test_default_web_max_pages():
    with patch.dict("os.environ", {
        "MISTRAL_API_KEY": "x",
        "POSTGRES_PASSWORD": "x",
    }):
        s = Settings()
        assert s.web_max_pages == 100


def test_web_max_pages_override():
    with patch.dict("os.environ", {
        "MISTRAL_API_KEY": "x",
        "POSTGRES_PASSWORD": "x",
        "WEB_MAX_PAGES": "50",
    }):
        s = Settings()
        assert s.web_max_pages == 50
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/test_web_loader.py -v
```

Expected: FAIL — `Settings` has no attribute `web_max_pages`

- [ ] **Step 3: Add setting**

In `src/rag/config/settings.py`, add after `retrieval_top_k`:

```python
    # Web loader
    web_max_pages: int = 100
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/unit/test_web_loader.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/rag/config/settings.py tests/unit/test_web_loader.py
git commit -m "feat(config): add web_max_pages setting"
```

---

## Task 3: Implement `web_loader.py`

**Files:**
- Create: `src/rag/rag/ingestion/web_loader.py`
- Modify: `tests/unit/test_web_loader.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_web_loader.py`:

```python
from unittest.mock import MagicMock, patch

from rag.rag.ingestion.web_loader import load_url


def _make_fake_docs(urls_and_texts: list[tuple[str, str]]):
    """Build fake LangChain Document objects."""
    docs = []
    for url, text in urls_and_texts:
        doc = MagicMock()
        doc.page_content = text
        doc.metadata = {"source": url}
        docs.append(doc)
    return docs


def test_load_url_returns_texts_and_metadata():
    fake_docs = _make_fake_docs([
        ("https://example.com", "Hello world"),
        ("https://example.com/about", "About page"),
    ])
    with patch(
        "rag.rag.ingestion.web_loader.RecursiveUrlLoader"
    ) as MockLoader:
        MockLoader.return_value.load.return_value = fake_docs
        texts, metadata = load_url("https://example.com", max_pages=10)

    assert texts == ["Hello world", "About page"]
    assert metadata["source"] == "https://example.com"
    assert metadata["pages_crawled"] == 2


def test_load_url_respects_max_pages():
    fake_docs = _make_fake_docs([
        ("https://example.com", f"Page {i}") for i in range(20)
    ])
    with patch(
        "rag.rag.ingestion.web_loader.RecursiveUrlLoader"
    ) as MockLoader:
        MockLoader.return_value.load.return_value = fake_docs
        texts, metadata = load_url("https://example.com", max_pages=5)

    assert len(texts) == 5
    assert metadata["pages_crawled"] == 5


def test_load_url_passes_correct_params_to_loader():
    with patch(
        "rag.rag.ingestion.web_loader.RecursiveUrlLoader"
    ) as MockLoader:
        MockLoader.return_value.load.return_value = []
        load_url("https://example.com/path", max_pages=42)

    call_kwargs = MockLoader.call_args.kwargs
    assert call_kwargs["url"] == "https://example.com/path"
    assert call_kwargs["max_depth"] == 10
    assert "example.com" in str(call_kwargs.get("link_regex", ""))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_web_loader.py::test_load_url_returns_texts_and_metadata \
              tests/unit/test_web_loader.py::test_load_url_respects_max_pages \
              tests/unit/test_web_loader.py::test_load_url_passes_correct_params_to_loader -v
```

Expected: FAIL — `web_loader` module not found

- [ ] **Step 3: Create `web_loader.py`**

Create `src/rag/rag/ingestion/web_loader.py`:

```python
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from langchain_community.document_loaders import RecursiveUrlLoader


def _extract_text(html: str) -> str:
    """Strip HTML tags and return plain text."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def load_url(url: str, max_pages: int) -> tuple[list[str], dict]:
    """Crawl a URL recursively within its domain and return page texts and metadata.

    Stays within the same domain as the starting URL. Crawl depth is effectively
    unlimited (max_depth=10) but bounded by max_pages.

    Returns:
        A tuple of (texts, metadata) where texts is a list of plain-text strings
        (one per crawled page) and metadata is a dict describing the crawl.
    """
    domain = urlparse(url).netloc
    link_regex = re.compile(rf"https?://{re.escape(domain)}")

    loader = RecursiveUrlLoader(
        url=url,
        max_depth=10,
        extractor=_extract_text,
        link_regex=link_regex,
    )
    docs = loader.load()
    docs = docs[:max_pages]

    texts = [doc.page_content for doc in docs]
    metadata = {
        "source": url,
        "type": "web",
        "domain": domain,
        "pages_crawled": len(docs),
    }
    return texts, metadata
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/test_web_loader.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/rag/rag/ingestion/web_loader.py tests/unit/test_web_loader.py
git commit -m "feat(ingestion): add web_loader with recursive URL crawling"
```

---

## Task 4: Add `ingest_url()` to `pipeline.py`

**Files:**
- Modify: `src/rag/rag/ingestion/pipeline.py`
- Modify: `tests/unit/test_ingestion_pipeline.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_ingestion_pipeline.py`:

```python
from rag.rag.ingestion.pipeline import _hash_url, ingest_url


def test_hash_url_is_deterministic():
    h1 = _hash_url("https://example.com")
    h2 = _hash_url("https://example.com")
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_hash_url_differs_for_different_urls():
    assert _hash_url("https://example.com") != _hash_url("https://other.com")


def test_hash_url_normalizes_trailing_slash():
    assert _hash_url("https://example.com") == _hash_url("https://example.com/")


@pytest.mark.asyncio
async def test_ingest_url_idempotent(mock_embeddings):
    mock_doc = MagicMock()
    mock_doc.id = "existing-id"
    mock_doc.filename = "https://example.com"

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_doc
    mock_db.execute.return_value = mock_result

    with patch("rag.rag.ingestion.pipeline.load_url", return_value=(["text"], {"source": "https://example.com", "pages_crawled": 1})):
        result = await ingest_url("https://example.com", mock_db)

    assert result.already_existed is True
    assert result.chunks_created == 0


@pytest.mark.asyncio
async def test_ingest_url_new_document(mock_embeddings):
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    mock_doc_instance = MagicMock()
    mock_doc_instance.id = "new-id"

    with patch("rag.rag.ingestion.pipeline.load_url", return_value=(["page text"], {"source": "https://example.com", "pages_crawled": 1})), \
         patch("rag.rag.ingestion.pipeline.Document", return_value=mock_doc_instance):
        result = await ingest_url("https://example.com", mock_db)

    assert result.already_existed is False
    assert result.chunks_created >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_ingestion_pipeline.py::test_hash_url_is_deterministic \
              tests/unit/test_ingestion_pipeline.py::test_ingest_url_idempotent -v
```

Expected: FAIL — `_hash_url` and `ingest_url` not defined

- [ ] **Step 3: Add `_hash_url()` and `ingest_url()` to `pipeline.py`**

Add to `src/rag/rag/ingestion/pipeline.py` after the existing imports and `_compute_hash`:

```python
from rag.rag.ingestion.web_loader import load_url
from rag.config.settings import get_settings


def _hash_url(url: str) -> str:
    """Return a SHA-256 hash of a normalized URL for deduplication."""
    normalized = url.rstrip("/").lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


async def ingest_url(url: str, db: AsyncSession) -> IngestionResult:
    """Ingest a web URL recursively into the vector store.

    Idempotent: re-ingesting the same URL (same normalized URL hash) is a no-op.
    """
    settings = get_settings()
    url_hash = _hash_url(url)

    # Check for existing document with same URL hash
    result = await db.execute(select(Document).where(Document.file_hash == url_hash))
    existing = result.scalar_one_or_none()
    if existing is not None:
        return IngestionResult(
            document_id=existing.id,
            filename=existing.filename,
            chunks_created=0,
            already_existed=True,
        )

    # Crawl + chunk
    pages, web_metadata = load_url(url, max_pages=settings.web_max_pages)
    chunks = chunk_texts(pages, source_metadata=web_metadata)

    if not chunks:
        raise ValueError(f"No text extracted from URL: {url}")

    # Persist document first to get its ID
    document = Document(filename=url, file_hash=url_hash, metadata_=web_metadata)
    db.add(document)
    await db.flush()

    # Embed all chunks in one batch call with Langfuse tracing
    texts = [c["content"] for c in chunks]
    langfuse = get_langfuse_client()
    with propagate_attributes(trace_name="document_embedding", session_id=str(document.id)):
        with langfuse.start_as_current_observation(
            name="embed_documents",
            as_type="embedding",
            model="mistral-embed",
            input=texts,
        ):
            embeddings = await mistral_embeddings.embed_documents(texts)

    db_chunks = [
        DocumentChunk(
            document_id=document.id,
            content=chunk["content"],
            embedding=embedding,
            chunk_index=chunk["chunk_index"],
            metadata_=chunk["metadata"],
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]
    db.add_all(db_chunks)
    await db.commit()

    return IngestionResult(
        document_id=document.id,
        filename=url,
        chunks_created=len(db_chunks),
        already_existed=False,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/test_ingestion_pipeline.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/rag/rag/ingestion/pipeline.py tests/unit/test_ingestion_pipeline.py
git commit -m "feat(ingestion): add ingest_url() with URL-based deduplication"
```

---

## Task 5: Add API endpoint `POST /documents/ingest-urls`

**Files:**
- Modify: `src/rag/api/routers/ingestion.py`
- Modify: `src/rag/rag/ingestion/pipeline.py` (add `max_pages` param to `ingest_url`)
- Modify: `tests/integration/test_api_ingestion.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/integration/test_api_ingestion.py`:

```python
@pytest.mark.asyncio
async def test_ingest_urls_returns_results(async_client: AsyncClient):
    fake_result = {
        "document_id": "00000000-0000-0000-0000-000000000001",
        "filename": "https://example.com",
        "chunks_created": 3,
        "already_existed": False,
    }
    with patch(
        "rag.api.routers.ingestion.ingest_url",
        new=AsyncMock(return_value=MagicMock(
            document_id="00000000-0000-0000-0000-000000000001",
            filename="https://example.com",
            chunks_created=3,
            already_existed=False,
        )),
    ):
        response = await async_client.post(
            "/api/v1/documents/ingest-urls",
            json={"urls": ["https://example.com"]},
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["filename"] == "https://example.com"
    assert data[0]["chunks_created"] == 3


@pytest.mark.asyncio
async def test_ingest_urls_empty_list_returns_empty(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/documents/ingest-urls",
        json={"urls": []},
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_ingest_urls_invalid_url_returns_422(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/documents/ingest-urls",
        json={"urls": ["not-a-url"]},
    )
    assert response.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/integration/test_api_ingestion.py::test_ingest_urls_returns_results \
              tests/integration/test_api_ingestion.py::test_ingest_urls_empty_list_returns_empty -v
```

Expected: FAIL — endpoint does not exist

- [ ] **Step 3: Add endpoint to `ingestion.py`**

Add to `src/rag/api/routers/ingestion.py`:

```python
from pydantic import BaseModel, HttpUrl

from rag.rag.ingestion.pipeline import ingest_url


class IngestUrlsRequest(BaseModel):
    urls: list[HttpUrl]
    max_pages: int | None = None


@router.post("/ingest-urls")
async def ingest_urls(
    request: IngestUrlsRequest,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    results = []
    for url in request.urls:
        result = await ingest_url(str(url), db)
        results.append({
            "document_id": str(result.document_id),
            "filename": result.filename,
            "chunks_created": result.chunks_created,
            "already_existed": result.already_existed,
        })
    return results
```

Note: `max_pages` from the request body overrides the setting. Pass it to `ingest_url` by updating
its signature to accept `max_pages: int | None = None` and using `settings.web_max_pages` as
fallback inside `ingest_url`. Update `ingest_url` in `pipeline.py` accordingly:

```python
async def ingest_url(url: str, db: AsyncSession, max_pages: int | None = None) -> IngestionResult:
    settings = get_settings()
    effective_max_pages = max_pages if max_pages is not None else settings.web_max_pages
    # ... replace settings.web_max_pages with effective_max_pages in load_url call
```

Also update the router to pass `max_pages`:

```python
result = await ingest_url(str(url), db, max_pages=request.max_pages)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/integration/test_api_ingestion.py -v
```

Expected: all PASS

- [ ] **Step 5: Run all tests**

```bash
uv run pytest -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/rag/api/routers/ingestion.py src/rag/rag/ingestion/pipeline.py \
        tests/integration/test_api_ingestion.py
git commit -m "feat(api): add POST /documents/ingest-urls endpoint"
```
