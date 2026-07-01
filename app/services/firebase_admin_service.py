import logging
from pathlib import Path

import firebase_admin
from firebase_admin import credentials
from flask import Flask

logger = logging.getLogger(__name__)


class FirebaseAdminService:
    """Initializes Firebase Admin SDK for backend services."""

    def __init__(self, project_id: str, credentials_path: str, base_dir: Path):
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.base_dir = base_dir

    @classmethod
    def from_app(cls, app: Flask) -> "FirebaseAdminService":
        return cls(
            project_id=app.config["FIREBASE_PROJECT_ID"],
            credentials_path=app.config["FIREBASE_CREDENTIALS_PATH"],
            base_dir=Path(app.root_path).parent,
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.project_id and self.credentials_path)

    def initialize(self) -> None:
        if firebase_admin._apps:
            logger.info("Firebase Admin SDK already initialized.")
            return

        if not self.is_configured:
            raise RuntimeError(
                "Firebase is not configured. Set FIREBASE_PROJECT_ID and "
                "FIREBASE_CREDENTIALS_PATH in .env.",
            )

        credentials_path = self._resolve_credentials_path()
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"Firebase service account file not found: {credentials_path}",
            )

        cred = credentials.Certificate(str(credentials_path))
        firebase_admin.initialize_app(cred, {"projectId": self.project_id})
        logger.info("Firebase Admin SDK initialized for project %s.", self.project_id)

    def _resolve_credentials_path(self) -> Path:
        path = Path(self.credentials_path)
        if path.is_absolute():
            return path
        return self.base_dir / path
