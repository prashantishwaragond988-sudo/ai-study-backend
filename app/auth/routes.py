from flask import Blueprint, request

from app.auth.firebase_middleware import firebase_auth_required
from app.auth.services import AuthProfileService
from app.auth.validators import optional_string, request_json, required_string
from app.common.responses import success_response

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.get("/me")
@firebase_auth_required
def me():
    profile = AuthProfileService().get_current_user(request.user_uid)
    return success_response({"user": profile})


@auth_bp.post("/profile")
@firebase_auth_required
def upsert_profile():
    payload = request_json(request.get_json(silent=True))
    profile = AuthProfileService().create_or_update_profile(
        uid=request.user_uid,
        name=required_string(payload, "name"),
        email=required_string(payload, "email"),
        mobile=required_string(payload, "mobile"),
        photo_url=optional_string(payload, "photoUrl"),
    )
    return success_response({"user": profile}, 201)


@auth_bp.post("/sync-verification")
@firebase_auth_required
def sync_verification():
    profile = AuthProfileService().sync_verification_status(request.user_uid)
    return success_response({"user": profile})


@auth_bp.post("/record-login")
@firebase_auth_required
def record_login():
    profile = AuthProfileService().record_login(request.user_uid)
    return success_response({"user": profile})


@auth_bp.post("/lookup-email")
def lookup_email():
    payload = request_json(request.get_json(silent=True))
    email = AuthProfileService().lookup_email_by_mobile(
        required_string(payload, "mobile"),
    )
    return success_response({"email": email})


@auth_bp.post("/logout")
@firebase_auth_required
def logout():
    return success_response({"message": "Logged out."})
