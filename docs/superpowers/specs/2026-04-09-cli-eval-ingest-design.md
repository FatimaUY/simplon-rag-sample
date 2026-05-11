# CLI — Evaluation and Ingestion

**Date:** 2026-04-09
**Status:** Approved

## Overview

Add two standalone CLI modules to run RAG evaluation and document ingestion outside the FastAPI
server, enabling cron scheduling or manual execution without a running API instance.

## File Structure

```
src/rag/cli/
  __init__.py          # empty
  _runner.py           # shared async session context manager
  eval.py              # python -m rag.cli.eval
  ingest.py            # python -m rag.cli.ingest

data/
  docs/                # PDF files to ingest (new folder, git-ignored content)
  evaluation/
    samples.json       # [{"question": "...", "ground_truth": "..."}, ...]
```

## `cli/_runner.py`

Provides an `async_session()` async context manager that:

- Reads settings via `get_settings()`
- Creates an `AsyncEngine` from `settings.database_url`
- Yields an `AsyncSession`
- Disposes the engine on exit

Rationale: `db/session.py` has module-level side effects (`logging.basicConfig`, engine creation at
import time) unsuitable for CLI use. `_runner.py` is a clean, lazy alternative.

## `cli/eval.py`

**Invocation:** `uv run python -m rag.cli.eval [--samples PATH]`

**Default samples path:** `data/evaluation/samples.json`

**Flow:**

1. Load `samples.json` — exit code `1` if missing or empty
2. Open async DB session via `_runner.async_session()`
3. Call `run_evaluation(samples, db)` from `evaluation/ragas_pipeline.py`
4. Log scores to stdout: `faithfulness=X  answer_relevancy=X  context_recall=X`
5. Push scores to Langfuse as a dataset run named `eval-YYYY-MM-DD` using `get_langfuse_client()`

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | `samples.json` missing or empty |
| `2` | DB or LLM error |

**No changes** to `evaluation/ragas_pipeline.py`.

## `cli/ingest.py`

**Invocation:** `uv run python -m rag.cli.ingest [--docs-dir PATH]`

**Default docs dir:** `data/docs/`

**Flow:**

1. Scan `--docs-dir` for `*.pdf` files
2. Open async DB session via `_runner.async_session()`
3. For each PDF call `ingest_pdf(path, db)` from `rag/ingestion/pipeline.py`:
   - Success → `[OK] filename.pdf — N chunks`
   - Already ingested → `[SKIP] filename.pdf — already ingested`
   - Exception → `[ERROR] filename.pdf — <message>`, continue
4. Print summary: `Ingested: N, Skipped: N, Errors: N`

**Exit code:** always `0` (errors are logged, not fatal).

**No changes** to `rag/ingestion/pipeline.py`.

## Cron Example

```cron
# Daily ingestion at 02:00
0 2 * * * cd /app && uv run python -m rag.cli.ingest >> /var/log/dsd-ingest.log 2>&1

# Weekly evaluation on Monday at 03:00
0 3 * * 1 cd /app && uv run python -m rag.cli.eval >> /var/log/dsd-eval.log 2>&1
```

## Data Files

### `data/evaluation/samples.json`

```json
[
  {
    "question": "How do I configure X?",
    "ground_truth": "To configure X, you need to..."
  }
]
```

### `data/docs/`

Drop PDF files here. Already-ingested files are skipped (idempotent via SHA-256 hash).

## Dependencies

No new Python packages required. All functionality uses existing modules:

- `rag.config.settings.get_settings`
- `rag.evaluation.ragas_pipeline.run_evaluation`
- `rag.rag.ingestion.pipeline.ingest_pdf`
- `rag.observability.langfuse_handler.get_langfuse_client`
