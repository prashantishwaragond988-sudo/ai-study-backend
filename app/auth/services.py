import logging
import random
import hmac
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter

from app.common.errors import AppError
from app.services.email_service import ResendEmailService
from app.services.jwt_service import JwtService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        email_service: ResendEmailService | None = None,
        jwt_service: JwtService | None = None,
    ):
        self._db = firestore.client()
        self._email_service = email_service
        self._jwt_service = jwt_service

    def register_user(self, payload: dict) -> dict:
        if self._email_service is None:
            raise AppError("Email service is not available.", 500)
        if not self._email_service.is_configured:
            raise AppError(
                "Email service is not configured. Set RESEND_API_KEY and EMAIL_FROM.",
                503,
            )

        self._ensure_unique_email(payload["email"])
        self._ensure_unique_mobile_number(payload["mobileNumber"])

        now = datetime.now(timezone.utc)
        user_ref = self._db.collection("users").document()
        password_hash = self._hash_password(payload["password"])

        user_ref.set(
            {
                "name": payload["name"],
                "email": payload["email"],
                "mobileNumber": payload["mobileNumber"],
                "passwordHash": password_hash,
                "emailVerified": False,
                "createdAt": now,
                "updatedAt": now,
            }
        )

        otp = self._generate_otp()
        otp_ref = self._store_registration_otp(email=payload["email"], otp=otp)
        try:
            self._email_service.send_registration_otp(
                name=payload["name"],
                email=payload["email"],
                otp=otp,
            )
        except AppError:
            user_ref.delete()
            otp_ref.delete()
            raise

        logger.info("Registered pending user %s.", payload["email"])
        return {
            "userId": user_ref.id,
            "email": payload["email"],
            "emailVerified": False,
        }

    def verify_email_otp(self, payload: dict) -> dict:
        otp_snapshot = self._find_latest_registration_otp(payload["email"])
        if otp_snapshot is None:
            raise AppError("Invalid OTP.", 400)

        otp_data = otp_snapshot.to_dict() or {}
        expires_at = otp_data.get("expiresAt")
        if expires_at is None or expires_at <= datetime.now(timezone.utc):
            otp_snapshot.reference.delete()
            raise AppError("OTP expired.", 400)

        if otp_data.get("otp") != payload["otp"]:
            raise AppError("Invalid OTP.", 400)

        user_snapshot = self._find_user_by_email(payload["email"])
        if user_snapshot is None:
            otp_snapshot.reference.delete()
            raise AppError("User not found for this OTP.", 404)

        now = datetime.now(timezone.utc)
        user_snapshot.reference.update(
            {
                "emailVerified": True,
                "updatedAt": now,
            }
        )
        otp_snapshot.reference.delete()

        logger.info("Verified registration email OTP for %s.", payload["email"])
        return {
            "userId": user_snapshot.id,
            "email": payload["email"],
            "emailVerified": True,
        }

    def login_user(self, payload: dict, *, device_info: str, ip_address: str) -> dict:
        jwt_service = self._require_jwt_service()
        user_snapshot = self._find_user_by_email(payload["email"])
        if user_snapshot is None:
            raise AppError("Invalid email or password.", 401)

        user_data = user_snapshot.to_dict() or {}
        if not self._verify_password(payload["password"], user_data.get("passwordHash", "")):
            raise AppError("Invalid email or password.", 401)

        if user_data.get("emailVerified") is not True:
            raise AppError("Email is not verified.", 403)

        session_id = uuid4().hex
        access_token = jwt_service.create_access_token(
            user_id=user_snapshot.id,
            email=user_data["email"],
        )
        refresh_token = jwt_service.create_refresh_token(
            user_id=user_snapshot.id,
            email=user_data["email"],
            session_id=session_id,
        )
        self._store_session(
            session_id=session_id,
            user_id=user_snapshot.id,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
        )

        logger.info("User %s logged in.", user_data["email"])
        return {
            "user": self._public_user(user_snapshot.id, user_data),
            "tokens": {
                "accessToken": access_token,
                "refreshToken": refresh_token,
                "expiresIn": jwt_service.access_expires_seconds,
            },
        }

    def refresh_access_token(self, payload: dict) -> dict:
        jwt_service = self._require_jwt_service()
        refresh_payload = jwt_service.decode_refresh_token(payload["refreshToken"])
        session_id = refresh_payload.get("sid")
        user_id = refresh_payload.get("sub")
        email = refresh_payload.get("email")
        if not session_id or not user_id or not email:
            raise AppError("Invalid refresh token.", 401)

        session_snapshot = self._get_active_session(session_id)
        session_data = session_snapshot.to_dict() or {}
        if session_data.get("userId") != user_id:
            raise AppError("Invalid refresh token.", 401)
        if not hmac.compare_digest(
            session_data.get("refreshTokenHash", ""),
            self._hash_refresh_token(payload["refreshToken"]),
        ):
            raise AppError("Invalid refresh token.", 401)

        expires_at = session_data.get("expiresAt")
        if expires_at is None or expires_at <= datetime.now(timezone.utc):
            session_snapshot.reference.update({"isActive": False})
            raise AppError("Refresh token expired.", 401)

        return {
            "accessToken": jwt_service.create_access_token(
                user_id=user_id,
                email=email,
            )
        }

    def logout_user(self, payload: dict) -> None:
        refresh_payload = self._require_jwt_service().decode_refresh_token(
            payload["refreshToken"],
        )
        session_id = refresh_payload.get("sid")
        if not session_id:
            raise AppError("Invalid refresh token.", 401)

        session_snapshot = self._get_active_session(session_id)
        session_data = session_snapshot.to_dict() or {}
        if not hmac.compare_digest(
            session_data.get("refreshTokenHash", ""),
            self._hash_refresh_token(payload["refreshToken"]),
        ):
            raise AppError("Invalid refresh token.", 401)

        session_snapshot.reference.update(
            {
                "isActive": False,
                "loggedOutAt": datetime.now(timezone.utc),
            }
        )
        logger.info("Session %s logged out.", session_id)

    def _ensure_unique_email(self, email: str) -> None:
        if self._find_user_by_email(email) is not None:
            raise AppError("Email already exists.", 409)

    def _ensure_unique_mobile_number(self, mobile_number: str) -> None:
        query = (
            self._db.collection("users")
            .where(filter=FieldFilter("mobileNumber", "==", mobile_number))
            .limit(1)
        )
        if len(list(query.stream())) > 0:
            raise AppError("Mobile number already exists.", 409)

    def _find_user_by_email(self, email: str):
        query = (
            self._db.collection("users")
            .where(filter=FieldFilter("email", "==", email))
            .limit(1)
        )
        users = list(query.stream())
        return users[0] if users else None

    def _get_active_session(self, session_id: str):
        session_snapshot = self._db.collection("user_sessions").document(session_id).get()
        if not session_snapshot.exists:
            raise AppError("Invalid refresh token.", 401)
        session_data = session_snapshot.to_dict() or {}
        if session_data.get("isActive") is not True:
            raise AppError("Invalid refresh token.", 401)
        return session_snapshot

    def _store_session(
        self,
        *,
        session_id: str,
        user_id: str,
        refresh_token: str,
        device_info: str,
        ip_address: str,
    ) -> None:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=self._require_jwt_service().refresh_expires_days)
        self._db.collection("user_sessions").document(session_id).set(
            {
                "sessionId": session_id,
                "userId": user_id,
                "refreshTokenHash": self._hash_refresh_token(refresh_token),
                "deviceInfo": device_info,
                "ipAddress": ip_address,
                "createdAt": now,
                "expiresAt": expires_at,
                "isActive": True,
            }
        )

    def _find_latest_registration_otp(self, email: str):
        query = (
            self._db.collection("otp_codes")
            .where(filter=FieldFilter("email", "==", email))
            .where(filter=FieldFilter("purpose", "==", "register"))
        )
        otp_codes = list(query.stream())
        if not otp_codes:
            return None
        return max(
            otp_codes,
            key=lambda snapshot: (snapshot.to_dict() or {}).get("createdAt"),
        )

    def _store_registration_otp(self, *, email: str, otp: str):
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=5)

        self._delete_existing_registration_otps(email)
        otp_ref = self._db.collection("otp_codes").document()
        otp_ref.set(
            {
                "email": email,
                "otp": otp,
                "purpose": "register",
                "expiresAt": expires_at,
                "createdAt": now,
            }
        )
        return otp_ref

    def _delete_existing_registration_otps(self, email: str) -> None:
        query = (
            self._db.collection("otp_codes")
            .where(filter=FieldFilter("email", "==", email))
            .where(filter=FieldFilter("purpose", "==", "register"))
        )
        for snapshot in query.stream():
            snapshot.reference.delete()

    def _hash_password(self, password: str) -> str:
        password_bytes = password.encode("utf-8")
        return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        if not password_hash:
            return False
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )

    def _hash_refresh_token(self, refresh_token: str) -> str:
        return hmac.new(
            self._require_jwt_service()._require_secret().encode("utf-8"),
            refresh_token.encode("utf-8"),
            sha256,
        ).hexdigest()

    def _public_user(self, user_id: str, user_data: dict) -> dict:
        return {
            "userId": user_id,
            "name": user_data.get("name", ""),
            "email": user_data.get("email", ""),
            "mobileNumber": user_data.get("mobileNumber", ""),
            "emailVerified": user_data.get("emailVerified") is True,
        }

    def _require_jwt_service(self) -> JwtService:
        if self._jwt_service is None:
            raise AppError("JWT service is not available.", 500)
        return self._jwt_service

    def _generate_otp(self) -> str:
        return f"{random.SystemRandom().randint(0, 999999):06d}"
