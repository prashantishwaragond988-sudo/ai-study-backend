from datetime import datetime, timezone
from uuid import uuid4

from firebase_admin import firestore
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from app.common.errors import AppError


class FirestoreService:
    """Firestore access layer for backend data operations."""

    def __init__(self):
        self._db = firestore.client()

    def write_and_read_test_document(self) -> dict:
        document_id = f"firestore-test-{uuid4().hex}"
        document_ref = self._db.collection("test").document(document_id)
        payload = {
            "message": "Firestore write/read test succeeded.",
            "source": "ai-study-backend",
            "createdAt": SERVER_TIMESTAMP,
            "clientCreatedAt": datetime.now(timezone.utc),
        }

        document_ref.set(payload)
        snapshot = document_ref.get()

        if not snapshot.exists:
            raise AppError("Firestore test document was not found after write.", 502)

        data = snapshot.to_dict() or {}
        return {"id": snapshot.id, **self._serialize_document(data)}

    def _serialize_document(self, data: dict) -> dict:
        serialized = {}
        for key, value in data.items():
            if hasattr(value, "isoformat"):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized
