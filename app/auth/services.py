from firebase_admin import auth, firestore
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from app.common.errors import AppError
from app.auth.validators import normalize_mobile, validate_email


class AuthProfileService:
    """Firebase Auth + Firestore profile operations for the Flask API."""

    def __init__(self):
        self._db = firestore.client()
        self._users = self._db.collection("users")

    def get_current_user(self, uid: str) -> dict:
        snapshot = self._users.document(uid).get()
        if not snapshot.exists:
            raise AppError("User profile not found.", 404)
        return self._serialize(snapshot.id, snapshot.to_dict() or {})

    def create_or_update_profile(
        self,
        *,
        uid: str,
        name: str,
        email: str,
        mobile: str,
        photo_url: str = "",
    ) -> dict:
        email = validate_email(email)
        mobile = normalize_mobile(mobile)
        self._ensure_unique_email(email, uid)
        self._ensure_unique_mobile(mobile, uid)

        firebase_user = auth.get_user(uid)
        email_verified = bool(firebase_user.email_verified)
        payload = {
            "uid": uid,
            "name": name.strip(),
            "email": email,
            "mobile": mobile,
            "phone": mobile,
            "photoUrl": photo_url or firebase_user.photo_url,
            "profileImage": photo_url or firebase_user.photo_url,
            "emailVerified": email_verified,
            "accountStatus": "Active" if email_verified else "Pending Verification",
            "provider": "password",
            "role": "student",
            "isActive": True,
            "updatedAt": SERVER_TIMESTAMP,
        }

        document = self._users.document(uid)
        if not document.get().exists:
            payload["createdAt"] = SERVER_TIMESTAMP
            payload["lastLogin"] = None
        document.set(payload, merge=True)
        return self.get_current_user(uid)

    def sync_verification_status(self, uid: str) -> dict:
        firebase_user = auth.get_user(uid)
        email_verified = bool(firebase_user.email_verified)
        self._users.document(uid).set(
            {
                "uid": uid,
                "email": firebase_user.email,
                "emailVerified": email_verified,
                "accountStatus": "Active" if email_verified else "Pending Verification",
                "updatedAt": SERVER_TIMESTAMP,
            },
            merge=True,
        )
        return self.get_current_user(uid)

    def record_login(self, uid: str) -> dict:
        firebase_user = auth.get_user(uid)
        if not firebase_user.email_verified:
            raise AppError("Please verify your email before continuing.", 403)
        self._users.document(uid).set(
            {
                "uid": uid,
                "emailVerified": True,
                "accountStatus": "Active",
                "lastLogin": SERVER_TIMESTAMP,
                "updatedAt": SERVER_TIMESTAMP,
            },
            merge=True,
        )
        return self.get_current_user(uid)

    def lookup_email_by_mobile(self, mobile: str) -> str:
        normalized = normalize_mobile(mobile)
        snapshots = self._users.where("mobile", "==", normalized).limit(1).stream()
        for snapshot in snapshots:
            email = (snapshot.to_dict() or {}).get("email")
            if email:
                return email
        snapshots = self._users.where("phone", "==", normalized).limit(1).stream()
        for snapshot in snapshots:
            email = (snapshot.to_dict() or {}).get("email")
            if email:
                return email
        raise AppError("User not found.", 404)

    def _ensure_unique_email(self, email: str, uid: str) -> None:
        for snapshot in self._users.where("email", "==", email).limit(1).stream():
            if snapshot.id != uid:
                raise AppError("Email already exists.", 409)

    def _ensure_unique_mobile(self, mobile: str, uid: str) -> None:
        for snapshot in self._users.where("mobile", "==", mobile).limit(1).stream():
            if snapshot.id != uid:
                raise AppError("Mobile number already exists.", 409)

    def _serialize(self, uid: str, data: dict) -> dict:
        serialized = {"id": uid}
        for key, value in data.items():
            if hasattr(value, "isoformat"):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized
