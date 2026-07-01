from functools import wraps

from firebase_admin import auth
from flask import request

from app.common.errors import AppError


def verify_firebase_token():
    """Require and verify a Firebase ID token for protected Flask APIs."""

    authorization = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise AppError("Missing Firebase ID token.", 401)

    id_token = authorization[len(prefix) :].strip()
    if not id_token:
        raise AppError("Missing Firebase ID token.", 401)

    try:
        decoded_token = auth.verify_id_token(id_token)
    except Exception as error:
        raise AppError("Invalid Firebase ID token.", 401) from error

    request.user_uid = decoded_token["uid"]
    request.firebase_user = decoded_token
    return decoded_token


def firebase_auth_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        verify_firebase_token()
        return view(*args, **kwargs)

    return wrapped
