from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_env_path)

@dataclass(frozen=True)
class Settings:
    env: str
    project_id: str
    firebase_project_id: str
    firebase_credentials_path: str
    firebase_storage_bucket: str
    storage_uploads_prefix: str
    storage_sanctions_prefix: str
    openai_api_key: str
    openai_model: str
    base_url: str
    disable_auth: bool
    local_storage_dir: str
    frontend_origin: str
    loan_signature_secret: str
    storage_signed_url_minutes: int


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y"}


def _get_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def get_settings() -> Settings:
    default_storage = str(Path(__file__).resolve().parents[1] / "static")
    return Settings(
        env=os.getenv("ENV", "local"),
        project_id=os.getenv("GCP_PROJECT_ID", ""),
        firebase_project_id=os.getenv("FIREBASE_PROJECT_ID", ""),
        firebase_credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
        firebase_storage_bucket=os.getenv("FIREBASE_STORAGE_BUCKET", ""),
        storage_uploads_prefix=os.getenv("FIREBASE_STORAGE_UPLOADS_PREFIX", "uploads"),
        storage_sanctions_prefix=os.getenv("FIREBASE_STORAGE_SANCTIONS_PREFIX", "letters"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        base_url=os.getenv("BASE_URL", "http://localhost:8000"),
        disable_auth=_get_bool("DISABLE_AUTH", True),
        local_storage_dir=_get_str("LOCAL_STORAGE_DIR", default_storage),
        frontend_origin=os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
        loan_signature_secret=os.getenv("LOAN_SIGNATURE_SECRET", ""),
        storage_signed_url_minutes=_get_int("STORAGE_SIGNED_URL_MINUTES", 60),
    )
