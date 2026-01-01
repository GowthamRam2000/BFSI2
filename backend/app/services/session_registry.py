from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from app.services.firebase import FirebaseService


class SessionRegistry:
    def __init__(self, firebase_service: FirebaseService) -> None:
        self._firebase = firebase_service
        self._memory: Dict[str, Dict[str, str]] = {}

    def get_active_session(self, uid: str) -> Optional[str]:
        if self._firebase.get_firestore() is None:
            record = self._memory.get(uid)
            return record.get("active_session_id") if record else None

        doc = (
            self._firebase.get_firestore()
            .collection("user_sessions")
            .document(uid)
            .get()
        )
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        return data.get("active_session_id")

    def set_active_session(self, uid: str, session_id: str) -> None:
        payload = {
            "active_session_id": session_id,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
        if self._firebase.get_firestore() is None:
            self._memory[uid] = payload
            return

        (
            self._firebase.get_firestore()
            .collection("user_sessions")
            .document(uid)
            .set(payload)
        )
