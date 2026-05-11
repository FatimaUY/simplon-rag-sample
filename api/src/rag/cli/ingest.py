"""CLI entry point for local PDF ingestion.

Usage:
    uv run python -m rag.cli.ingest
    uv run python -m rag.cli.ingest --docs-dir path/to/docs/

Exit codes:
    0 — always (individual errors are reported and skipped)
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from rag.cli._runner import async_session
from rag.rag.ingestion.pipeline import ingest_pdf

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DOCS_DIR = _PROJECT_ROOT / "data" / "docs"

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest PDF files into the vector store")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        required=False,
        default=DEFAULT_DOCS_DIR,
        help=f"Directory containing PDF files (default: {DEFAULT_DOCS_DIR})",
    )
    return parser.parse_args()


@dataclass
class _Summary:
    ingested: int = 0
    skipped: int = 0
    errors: int = 0
    files: list[Path] = field(default_factory=list)


async def _run(docs_dir: Path) -> None:
    if not docs_dir.exists():
        print(f"Docs directory not found: {docs_dir}")
        return

    pdfs = sorted(docs_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found in {docs_dir}")
        return

    print(f"Found {len(pdfs)} PDF file(s) in {docs_dir}")
    summary = _Summary(files=pdfs)

    async with async_session() as db:
        for pdf in pdfs:
            try:
                result = await ingest_pdf(pdf, db)
                if result.already_existed:
                    print(f"[SKIP]  {pdf.name} — already ingested")
                    summary.skipped += 1
                else:
                    print(f"[OK]    {pdf.name} — {result.chunks_created} chunks")
                    summary.ingested += 1
            except Exception as exc:
                print(f"[ERROR] {pdf.name} — {exc}")
                summary.errors += 1

    print(f"\nDone. Ingested: {summary.ingested}, Skipped: {summary.skipped}, Errors: {summary.errors}")


def main() -> None:
    args = _parse_args()
    asyncio.run(_run(args.docs_dir))


if __name__ == "__main__":
    main()
