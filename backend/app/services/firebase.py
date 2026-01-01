from __future__ import annotations

from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import auth, credentials, firestore

from app.config import get_settings


class FirebaseService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._app = None
        self._firestore = None
        self._init_app()

    def _init_app(self) -> None:
        if self.settings.disable_auth:
            return
        if firebase_admin._apps:
            self._app = firebase_admin.get_app()
        else:
            if not self.settings.firebase_credentials_path:
                raise RuntimeError("Missing GOOGLE_APPLICATION_CREDENTIALS for Firebase.")
            cred = credentials.Certificate(self.settings.firebase_credentials_path)
            self._app = firebase_admin.initialize_app(
                cred, {"projectId": self.settings.firebase_project_id or None}
            )
        self._firestore = firestore.client(app=self._app)

    def get_firestore(self):
        return self._firestore

    def verify_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        if self.settings.disable_auth:
            return {"uid": "local-user"}
        if not id_token:
            return None
        try:
            return auth.verify_id_token(id_token)
        except Exception:
            return None
