from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from flask import Flask

from app.common.errors import AppError


class JwtService:
    """Issues and verifies access/refresh JWTs."""

    def __init__(
        self,
        secret_key: str,
        access_expires_minutes: int,
        refresh_expires_days: int,
    ):
        self.secret_key = secret_key
        self.access_expires_minutes = access_expires_minutes
        self.refresh_expires_days = refresh_expires_days
        self.algorithm = "HS256"

    @classmethod
    def from_app(cls, app: Flask) -> "JwtService":
        return cls(
            secret_key=app.config["JWT_SECRET_KEY"],
            access_expires_minutes=app.config["JWT_ACCESS_TOKEN_EXPIRES_MINUTES"],
            refresh_expires_days=app.config["JWT_REFRESH_TOKEN_EXPIRES_DAYS"],
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.secret_key and self.secret_key != "change-this-before-production")

    @property
    def access_expires_seconds(self) -> int:
        return self.access_expires_minutes * 60

    def create_access_token(self, *, user_id: str, email: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self.access_expires_minutes),
        }
        return jwt.encode(payload, self._require_secret(), algorithm=self.algorithm)

    def create_refresh_token(self, *, user_id: str, email: str, session_id: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "email": email,
            "sid": session_id,
            "type": "refresh",
            "jti": uuid4().hex,
            "iat": now,
            "exp": now + timedelta(days=self.refresh_expires_days),
        }
        return jwt.encode(payload, self._require_secret(), algorithm=self.algorithm)

    def decode_refresh_token(self, refresh_token: str) -> dict:
        try:
            payload = jwt.decode(
                refresh_token,
                self._require_secret(),
                algorithms=[self.algorithm],
            )
        except jwt.ExpiredSignatureError as error:
            raise AppError("Refresh token expired.", 401) from error
        except jwt.InvalidTokenError as error:
            raise AppError("Invalid refresh token.", 401) from error

        if payload.get("type") != "refresh":
            raise AppError("Invalid refresh token.", 401)
        return payload

    def _require_secret(self) -> str:
        if not self.is_configured:
            raise AppError(
                "JWT service is not configured. Set JWT_SECRET_KEY in .env.",
                503,
            )
        return self.secret_key
