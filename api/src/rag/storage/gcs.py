"""Helper GCS pour l'émulateur local et GCP réel."""

import os
from pathlib import Path

from google.cloud import storage

from google.auth.credentials import AnonymousCredentials

def _get_client() -> storage.Client:
    endpoint = os.getenv("GCS_ENDPOINT_URL") or os.getenv("STORAGE_EMULATOR_HOST")
    if endpoint:
        return storage.Client(
            project="local",
            credentials=AnonymousCredentials(),
            client_options={"api_endpoint": endpoint}
        )
    return storage.Client()


def get_bucket(bucket_name: str | None = None) -> storage.Bucket:
    name = bucket_name or os.getenv("GCS_BUCKET_NAME", "simplon-fatima-corpus")
    client = storage.Client()
    return client.bucket(name)


def upload_pdf(local_path: Path, bucket_name: str | None = None) -> str:
    """Upload un PDF vers GCS."""
    bucket = get_bucket(bucket_name)
    blob = bucket.blob(local_path.name)
    blob.upload_from_filename(str(local_path))
    return f"gs://{bucket.name}/{local_path.name}"


def download_all_pdfs(local_dir: Path, bucket_name: str | None = None) -> list[Path]:
    """Télécharge tous les PDFs du bucket vers le dossier local."""
    bucket = get_bucket(bucket_name)
    local_dir.mkdir(parents=True, exist_ok=True)
    
    blobs = [b for b in bucket.list_blobs() if b.name.endswith(".pdf")]
    if not blobs:
        print(f"[GCS] Aucun PDF dans le bucket")
        return []
    
    downloaded = []
    for blob in blobs:
        local_path = local_dir / blob.name
        if not local_path.exists():
            blob.download_to_filename(str(local_path))
            downloaded.append(local_path)
            print(f"[GCS] Téléchargé : {blob.name}")
        else:
            print(f"[GCS] Déjà présent : {blob.name}")
    
    return downloaded


def list_pdfs(bucket_name: str | None = None) -> list[str]:
    """Liste les noms des PDFs dans le bucket."""
    bucket = get_bucket(bucket_name)
    return [b.name for b in bucket.list_blobs() if b.name.endswith(".pdf")]