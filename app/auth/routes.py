from flask import Blueprint, current_app, request

from app.auth.services import AuthService
from app.auth.validators import (
    validate_email_otp_payload,
    validate_login_payload,
    validate_registration_payload,
    validate_refresh_token_payload,
)
from app.common.responses import success_response
from app.services.email_service import EmailService
from app.services.jwt_service import JwtService

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    payload = validate_registration_payload(request.get_json(silent=True) or {})
    auth_service = AuthService(email_service=EmailService.from_app(current_app))
    user = auth_service.register_user(payload)
    return success_response(
        {
            "message": "Registration created. Verification OTP sent to email.",
            "user": user,
        },
        201,
    )


@auth_bp.post("/verify-email-otp")
def verify_email_otp():
    payload = validate_email_otp_payload(request.get_json(silent=True) or {})
    auth_service = AuthService(email_service=EmailService.from_app(current_app))
    user = auth_service.verify_email_otp(payload)
    return success_response(
        {
            "message": "Email verified successfully.",
            "user": user,
        }
    )


@auth_bp.post("/login")
def login():
    payload = validate_login_payload(request.get_json(silent=True) or {})
    auth_service = AuthService(jwt_service=JwtService.from_app(current_app))
    result = auth_service.login_user(
        payload,
        device_info=request.headers.get("User-Agent", "Unknown device"),
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr or ""),
    )
    return success_response(
        {
            "message": "Login successful.",
            "user": result["user"],
            "tokens": result["tokens"],
        }
    )


@auth_bp.post("/refresh-token")
def refresh_token():
    payload = validate_refresh_token_payload(request.get_json(silent=True) or {})
    auth_service = AuthService(jwt_service=JwtService.from_app(current_app))
    tokens = auth_service.refresh_access_token(payload)
    return success_response(tokens)


@auth_bp.post("/logout")
def logout():
    payload = validate_refresh_token_payload(request.get_json(silent=True) or {})
    auth_service = AuthService(jwt_service=JwtService.from_app(current_app))
    auth_service.logout_user(payload)
    return success_response({"message": "Logged out successfully."})
