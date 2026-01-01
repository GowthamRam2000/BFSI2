from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate backend .env settings")
    parser.add_argument("--env-file", default=None, help="Path to .env file")
    parser.add_argument("--skip-openai", action="store_true", help="Skip OpenAI check")
    parser.add_argument("--skip-firestore", action="store_true", help="Skip Firestore check")
    parser.add_argument("--skip-storage", action="store_true", help="Skip Firebase Storage check")
    args = parser.parse_args()

    env_path = Path(args.env_file) if args.env_file else Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        print(f"[FAIL] Env file not found: {env_path}")
        return 1

    load_dotenv(env_path)

    results: List[CheckResult] = []

    def add_result(name: str, ok: bool, detail: str, status: Optional[str] = None) -> None:
        status_text = status or ("OK" if ok else "FAIL")
        results.append(CheckResult(name=name, status=status_text, detail=detail))
        print(f"[{status_text}] {name} - {detail}")

    required = [
        "ENV",
        "BASE_URL",
        "FRONTEND_ORIGIN",
        "OPENAI_MODEL",
        "OPENAI_API_KEY",
        "FIREBASE_PROJECT_ID",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "FIREBASE_STORAGE_BUCKET",
        "FIREBASE_STORAGE_UPLOADS_PREFIX",
        "FIREBASE_STORAGE_SANCTIONS_PREFIX",
        "LOAN_SIGNATURE_SECRET",
    ]

    missing = [name for name in required if not os.getenv(name)]
    if missing:
        add_result("Env vars", False, f"Missing: {', '.join(missing)}")
    else:
        add_result("Env vars", True, "All required vars present")

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        if Path(credentials_path).exists():
            add_result("Service account", True, f"Found {credentials_path}")
        else:
            add_result("Service account", False, f"Missing file {credentials_path}")

    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "")
    if bucket_name.startswith("gs://"):
        add_result(
            "Bucket name",
            False,
            "Bucket should not include gs:// prefix",
        )

    if not args.skip_storage:
        add_result("Storage", *check_storage())
    else:
        add_result("Storage", True, "Skipped", status="SKIP")

    if not args.skip_firestore:
        add_result("Firestore", *check_firestore())
    else:
        add_result("Firestore", True, "Skipped", status="SKIP")

    if not args.skip_openai:
        add_result("OpenAI", *check_openai())
    else:
        add_result("OpenAI", True, "Skipped", status="SKIP")

    failed = [r for r in results if r.status == "FAIL"]
    return 1 if failed else 0


def check_storage() -> tuple[bool, str]:
    try:
        from google.cloud import storage
    except Exception as exc:
        return False, f"google-cloud-storage import failed: {exc}"

    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
    uploads_prefix = os.getenv("FIREBASE_STORAGE_UPLOADS_PREFIX", "uploads")
    sanctions_prefix = os.getenv("FIREBASE_STORAGE_SANCTIONS_PREFIX", "letters")
    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("FIREBASE_PROJECT_ID")

    if not bucket_name:
        return False, "FIREBASE_STORAGE_BUCKET is empty"

    try:
        client = storage.Client(project=project_id or None)
        bucket = client.bucket(bucket_name)
        if not bucket.exists():
            return False, f"Bucket not found: {bucket_name}"

        uploads_status = _check_prefix(client, bucket_name, uploads_prefix)
        sanctions_status = _check_prefix(client, bucket_name, sanctions_prefix)

        detail = (
            f"Bucket OK. {uploads_prefix}/{uploads_status}; "
            f"{sanctions_prefix}/{sanctions_status}"
        )
        return True, detail
    except Exception as exc:
        return False, f"Storage check failed: {exc}"


def _check_prefix(client, bucket_name: str, prefix: str) -> str:
    normalized = prefix.strip("/")
    iterator = client.list_blobs(bucket_name, prefix=f"{normalized}/", max_results=1)
    found = next(iterator, None)
    return "found" if found else "no objects (ok)"


def check_firestore() -> tuple[bool, str]:
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except Exception as exc:
        return False, f"firebase-admin import failed: {exc}"

    project_id = os.getenv("FIREBASE_PROJECT_ID")
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not project_id or not cred_path:
        return False, "Missing FIREBASE_PROJECT_ID or GOOGLE_APPLICATION_CREDENTIALS"

    try:
        if firebase_admin._apps:
            app = firebase_admin.get_app()
        else:
            cred = credentials.Certificate(cred_path)
            app = firebase_admin.initialize_app(cred, {"projectId": project_id})
        db = firestore.client(app=app)
        _ = db.collection("_health").document("ping").get()
        return True, "Firestore reachable"
    except Exception as exc:
        return False, f"Firestore check failed: {exc}"


def check_openai() -> tuple[bool, str]:
    try:
        from openai import OpenAI
    except Exception as exc:
        return False, f"openai import failed: {exc}"

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False, "OPENAI_API_KEY is empty"

    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        count = len(models.data) if hasattr(models, "data") else 0
        return True, f"OpenAI reachable (models: {count})"
    except Exception as exc:
        return False, f"OpenAI check failed: {exc}"


if __name__ == "__main__":
    sys.exit(main())
