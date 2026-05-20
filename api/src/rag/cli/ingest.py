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
import os
from dataclasses import dataclass, field
from pathlib import Path
from rag.cli._runner import async_session
from rag.rag.ingestion.pipeline import ingest_pdf

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DOCS_DIR = _PROJECT_ROOT / "data" / "docs"
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "simplon-fatima-corpus")


def _get_gcs_client():
    """Retourne un client GCS ou fake-gcs selon l'environnement."""
    from google.cloud import storage
    endpoint = os.getenv("GCS_ENDPOINT_URL")
    if endpoint:
        client = storage.Client(
            project="local",
            client_options={"api_endpoint": endpoint}
        )
    else:
        client = storage.Client()
    return client


def _sync_from_gcs(local_dir: Path, bucket_name: str) -> None:
    """Télécharge les PDFs depuis GCS si absents en local."""
    try:
        client = _get_gcs_client()
        bucket = client.bucket(bucket_name)
        local_dir.mkdir(parents=True, exist_ok=True)
        blobs = list(bucket.list_blobs())
        if not blobs:
            print(f"[GCS] Bucket vide : {bucket_name}")
            return
        for blob in blobs:
            if not blob.name.endswith(".pdf"):
                continue
            local_path = local_dir / blob.name
            if not local_path.exists():
                blob.download_to_filename(str(local_path))
                print(f"[GCS] Téléchargé : {blob.name}")
            else:
                print(f"[GCS] Déjà présent : {blob.name}")
    except Exception as exc:
        print(f"[GCS] Erreur sync : {exc}")


def _upload_to_gcs(pdf_path: Path, bucket_name: str) -> None:
    """Upload un PDF vers GCS après ingestion."""
    try:
        client = _get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(pdf_path.name)
        blob.upload_from_filename(str(pdf_path))
        print(f"[GCS] Uploadé : {pdf_path.name}")
    except Exception as exc:
        print(f"[GCS] Erreur upload : {exc}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest PDF files into the vector store")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        required=False,
        default=DEFAULT_DOCS_DIR,
        help=f"Directory containing PDF files (default: {DEFAULT_DOCS_DIR})",
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


async def _run(docs_dir: Path, skip_gcs: bool = False) -> None:
    if not skip_gcs:
        print(f"[GCS] Synchronisation depuis gs://{GCS_BUCKET_NAME}...")
        _sync_from_gcs(docs_dir, GCS_BUCKET_NAME)

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
                    if not skip_gcs:
                        _upload_to_gcs(pdf, GCS_BUCKET_NAME)
            except Exception as exc:
                print(f"[ERROR] {pdf.name} — {exc}")
                summary.errors += 1

    print(f"\nDone. Ingested: {summary.ingested}, Skipped: {summary.skipped}, Errors: {summary.errors}")


def main() -> None:
    args = _parse_args()
    asyncio.run(_run(args.docs_dir, skip_gcs=args.skip_gcs))


if __name__ == "__main__":
    main()
