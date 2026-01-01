from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Optional

from google.cloud import storage

from app.config import get_settings


class StorageClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._gcs_client = None
        self._bucket_name = _normalize_bucket(self.settings.firebase_storage_bucket)
        if self._bucket_name:
            self._gcs_client = storage.Client(project=self.settings.project_id or None)

    def upload_bytes(
        self,
        data: bytes,
        object_path: str,
        content_type: str,
        signed_url: bool = False,
    ) -> str:
        object_path = object_path.lstrip("/")
        if self._gcs_client:
            bucket = self._gcs_client.bucket(self._bucket_name)
            blob = bucket.blob(object_path)
            blob.upload_from_string(data, content_type=content_type)
            if signed_url:
                return _signed_url(blob, self.settings.storage_signed_url_minutes)
            return _public_url(self._bucket_name, object_path)

        local_dir = Path(self.settings.local_storage_dir)
        file_path = local_dir / object_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        base_url = self.settings.base_url.rstrip("/")
        return f"{base_url}/static/{object_path}"

    def upload_uploads(
        self, data: bytes, filename: str, content_type: str, owner_id: Optional[str] = None
    ) -> str:
        prefix = self.settings.storage_uploads_prefix.strip("/")
        object_path = _scoped_path(prefix, filename, owner_id)
        return self.upload_bytes(data, object_path, content_type, signed_url=False)

    def upload_sanctions(
        self, data: bytes, filename: str, content_type: str, owner_id: Optional[str] = None
    ) -> str:
        prefix = self.settings.storage_sanctions_prefix.strip("/")
        object_path = _scoped_path(prefix, filename, owner_id)
        return self.upload_bytes(data, object_path, content_type, signed_url=True)

    def upload_file(self, file_path: str, filename: Optional[str] = None) -> str:
        path = Path(file_path)
        data = path.read_bytes()
        name = filename or path.name
        content_type = _guess_content_type(name)
        return self.upload_bytes(data, name, content_type, signed_url=False)


def _guess_content_type(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "application/pdf"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    return "application/octet-stream"


def _scoped_path(prefix: str, filename: str, owner_id: Optional[str]) -> str:
    safe_owner = _sanitize_segment(owner_id) if owner_id else None
    if safe_owner:
        return f"{prefix}/{safe_owner}/{filename}"
    return f"{prefix}/{filename}"


def _sanitize_segment(value: Optional[str]) -> str:
    if not value:
        return ""
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)


def _normalize_bucket(bucket: str) -> str:
    if not bucket:
        return ""
    value = bucket.strip()
    if value.startswith("gs://"):
        value = value[5:]
    return value.strip("/")


def _public_url(bucket: str, object_path: str) -> str:
    return f"https://storage.googleapis.com/{bucket}/{object_path}"


def _signed_url(blob: storage.Blob, minutes: int) -> str:
    try:
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=minutes),
            method="GET",
        )
    except Exception:
        return _public_url(blob.bucket.name, blob.name)
