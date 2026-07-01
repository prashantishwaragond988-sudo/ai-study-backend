import re

from app.common.errors import AppError

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
MOBILE_PATTERN = re.compile(r"^\+?[0-9]{10,15}$")


def validate_registration_payload(payload: dict) -> dict:
    errors = {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    mobile_number = str(payload.get("mobileNumber", "")).strip()
    password = str(payload.get("password", ""))

    if not name:
        errors["name"] = "Full name is required."
    if not email:
        errors["email"] = "Email is required."
    elif not EMAIL_PATTERN.match(email):
        errors["email"] = "Enter a valid email address."
    if not mobile_number:
        errors["mobileNumber"] = "Mobile number is required."
    elif not MOBILE_PATTERN.match(mobile_number):
        errors["mobileNumber"] = "Enter a valid mobile number with 10 to 15 digits."
    if not password:
        errors["password"] = "Password is required."
    elif len(password) < 8:
        errors["password"] = "Password must be at least 8 characters."

    if errors:
        raise AppError("Validation failed.", 400, errors)

    return {
        "name": name,
        "email": email,
        "mobileNumber": mobile_number,
        "password": password,
    }


def validate_email_otp_payload(payload: dict) -> dict:
    errors = {}
    email = str(payload.get("email", "")).strip().lower()
    otp = str(payload.get("otp", "")).strip()

    if not email:
        errors["email"] = "Email is required."
    elif not EMAIL_PATTERN.match(email):
        errors["email"] = "Enter a valid email address."
    if not otp:
        errors["otp"] = "OTP is required."
    elif not re.fullmatch(r"[0-9]{6}", otp):
        errors["otp"] = "OTP must be a 6-digit code."

    if errors:
        raise AppError("Validation failed.", 400, errors)

    return {"email": email, "otp": otp}


def validate_login_payload(payload: dict) -> dict:
    errors = {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))

    if not email:
        errors["email"] = "Email is required."
    elif not EMAIL_PATTERN.match(email):
        errors["email"] = "Enter a valid email address."
    if not password:
        errors["password"] = "Password is required."

    if errors:
        raise AppError("Validation failed.", 400, errors)

    return {"email": email, "password": password}


def validate_refresh_token_payload(payload: dict) -> dict:
    refresh_token = str(payload.get("refreshToken", "")).strip()
    if not refresh_token:
        raise AppError(
            "Validation failed.",
            400,
            {"refreshToken": "Refresh token is required."},
        )
    return {"refreshToken": refresh_token}
