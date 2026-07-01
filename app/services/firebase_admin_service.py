import base64
import binascii
import json
import logging
from pathlib import Path

import firebase_admin
from firebase_admin import credentials
from flask import Flask

logger = logging.getLogger(__name__)


class FirebaseAdminService:
    """Initializes Firebase Admin SDK for backend services."""

    def __init__(
        self,
        project_id: str,
        credentials_path: str,
        base_dir: Path,
        service_account_base64: str = "",
    ):
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.base_dir = base_dir
        self.service_account_base64 = service_account_base64

    @classmethod
    def from_app(cls, app: Flask) -> "FirebaseAdminService":
        return cls(
            project_id=app.config["FIREBASE_PROJECT_ID"],
            credentials_path=app.config["FIREBASE_CREDENTIALS_PATH"],
            service_account_base64=app.config.get("FIREBASE_SERVICE_ACCOUNT_BASE64", ""),
            base_dir=Path(app.root_path).parent,
        )

    @property
    def is_configured(self) -> bool:
        return bool(
            self.project_id
            and (self.service_account_base64.strip() or self.credentials_path)
        )

    def initialize(self) -> None:
        if firebase_admin._apps:
            logger.info("Firebase Admin SDK already initialized.")
            return

        if not self.is_configured:
            raise RuntimeError(
                "Firebase is not configured. Set FIREBASE_PROJECT_ID and "
                "FIREBASE_SERVICE_ACCOUNT_BASE64 or FIREBASE_CREDENTIALS_PATH.",
            )

        cred = self._load_credentials()
        firebase_admin.initialize_app(cred, {"projectId": self.project_id})
        logger.info("Firebase Admin SDK initialized for project %s.", self.project_id)

    def _load_credentials(self) -> credentials.Certificate:
        if self.service_account_base64.strip():
            service_account = self._decode_service_account_base64()
            logger.info("Loading Firebase Admin credentials from base64 environment.")
            return credentials.Certificate(service_account)

        credentials_path = self._resolve_credentials_path()
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"Firebase service account file not found: {credentials_path}",
            )

        logger.info("Loading Firebase Admin credentials from %s.", credentials_path)
        return credentials.Certificate(str(credentials_path))

    def _decode_service_account_base64(self) -> dict:
        try:
            decoded = base64.b64decode(
                self.service_account_base64.strip(),
                validate=True,
            ).decode("utf-8")
            service_account = json.loads(decoded)
        except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_BASE64 must be a valid base64-encoded "
                "Firebase service account JSON file.",
            ) from error

        if not isinstance(service_account, dict):
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_BASE64 must decode to a JSON object.",
            )
        return service_account

    def _resolve_credentials_path(self) -> Path:
        path = Path(self.credentials_path)
        if path.is_absolute():
            return path
        return self.base_dir / path
