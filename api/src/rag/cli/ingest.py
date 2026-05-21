"""CLI entry point for local PDF ingestion with GCS support.
Usage:
    uv run python -m rag.cli.ingest
    uv run python -m rag.cli.ingest --docs-dir path/to/docs/
    uv run python -m rag.cli.ingest --from-gcs
    uv run python -m rag.cli.ingest --skip-gcs
Exit codes:
    0 — always (individual errors are reported and skipped)
"""

from __future__ import annotations

import argparse
import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path

from rag.cli._runner import async_session
from rag.rag.ingestion.pipeline import ingest_pdf
from rag.storage.gcs import download_all_pdfs, upload_pdf

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DOCS_DIR = _PROJECT_ROOT / "data" / "docs"
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "simplon-fatima-corpus")


def _is_gcs_configured() -> bool:
    """Vrai si GCS est explicitement configuré."""
    return bool(os.getenv("GCS_BUCKET_NAME") or os.getenv("GCS_ENDPOINT_URL"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest PDF files into the vector store"
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        required=False,
        default=DEFAULT_DOCS_DIR,
        help=f"Directory containing PDF files (default: {DEFAULT_DOCS_DIR})",
    )
    parser.add_argument(
        "--from-gcs",
        action="store_true",
        help="Télécharger les PDFs depuis GCS avant ingestion",
    )
    parser.add_argument(
        "--skip-gcs",
        action="store_true",
        help="Ne pas synchroniser avec GCS",
    )
    return parser.parse_args()


@dataclass
class _Summary:
    ingested: int = 0
    skipped: int = 0
    errors: int = 0
    files: list[Path] = field(default_factory=list)


async def _run(docs_dir: Path, from_gcs: bool = False, skip_gcs: bool = False) -> None:
    # === SYNC DEPUIS GCS ===
    if from_gcs and _is_gcs_configured():
        print(f"[GCS] Téléchargement depuis gs://{GCS_BUCKET_NAME}...")
        download_all_pdfs(docs_dir, GCS_BUCKET_NAME)
    elif from_gcs:
        print("[GCS] Non configuré, --from-gcs ignoré")

    if not docs_dir.exists():
        print(f"Docs directory not found: {docs_dir}")
        return

    pdfs = sorted(docs_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found in {docs_dir}")
        return

    print(f"Found {len(pdfs)} PDF file(s) in {docs_dir}")
    summary = _Summary(files=pdfs)

    # === INGESTION ===
    async with async_session() as db:
        for pdf in pdfs:
            try:
                # Upload GCS AVANT ingestion (GCS = source de vérité)
                if not skip_gcs and _is_gcs_configured():
                    try:
                        upload_pdf(pdf, GCS_BUCKET_NAME)
                        print(f"[GCS] Uploadé : {pdf.name}")
                    except Exception as exc:
                        print(f"[GCS] Erreur upload {pdf.name} : {exc}")
                        # On continue quand même l'ingestion locale

                # Ingestion dans la base vectorielle
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

    print(
        f"\nDone. Ingested: {summary.ingested}, Skipped: {summary.skipped}, Errors: {summary.errors}"
    )


def main() -> None:
    args = _parse_args()
    asyncio.run(_run(args.docs_dir, from_gcs=args.from_gcs, skip_gcs=args.skip_gcs))


if __name__ == "__main__":
    main()
