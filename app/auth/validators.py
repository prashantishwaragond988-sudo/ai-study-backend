import re

from app.common.errors import AppError


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def request_json(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        raise AppError("Request body must be a JSON object.", 400)
    return payload


def required_string(payload: dict, field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise AppError(f"{field} is required.", 400)
    return value.strip()


def optional_string(payload: dict, field: str) -> str:
    value = payload.get(field)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise AppError(f"{field} must be a string.", 400)
    return value.strip()


def validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if not EMAIL_RE.match(normalized):
        raise AppError("Invalid email.", 400)
    return normalized


def normalize_mobile(mobile: str) -> str:
    trimmed = mobile.strip()
    has_plus = trimmed.startswith("+")
    digits = re.sub(r"\D", "", trimmed)
    if len(digits) < 10 or len(digits) > 15:
        raise AppError("Invalid mobile number.", 400)
    return f"+{digits}" if has_plus else digits
