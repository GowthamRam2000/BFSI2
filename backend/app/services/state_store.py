from __future__ import annotations

import copy
from typing import Any, Dict

from app.services.firebase import FirebaseService


class StateStore:
    def __init__(self, firebase_service: FirebaseService) -> None:
        self._firebase = firebase_service
        self._memory: Dict[str, Dict[str, Any]] = {}

    def load(self, session_id: str) -> Dict[str, Any] | None:
        if self._firebase.get_firestore() is None:
            state = self._memory.get(session_id)
            return copy.deepcopy(state) if state else None

        doc = (
            self._firebase.get_firestore()
            .collection("chat_sessions")
            .document(session_id)
            .get()
        )
        if not doc.exists:
            return None
        return doc.to_dict()

    def save(self, session_id: str, state: Dict[str, Any]) -> None:
        if self._firebase.get_firestore() is None:
            self._memory[session_id] = copy.deepcopy(state)
            return

        (
            self._firebase.get_firestore()
            .collection("chat_sessions")
            .document(session_id)
            .set(state)
        )
