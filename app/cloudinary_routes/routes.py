from flask import Blueprint, request

from app.auth.firebase_middleware import firebase_auth_required
from app.common.errors import AppError
from app.common.responses import success_response
from app.services.cloudinary_service import CloudinaryService

cloudinary_bp = Blueprint("cloudinary", __name__, url_prefix="/api/cloudinary")


@cloudinary_bp.post("/upload")
@firebase_auth_required
def upload_asset():
    if "file" not in request.files:
        raise AppError("File is required.")
    folder = request.form.get("folder", "").strip()
    resource_type = request.form.get("resourceType", "auto").strip()
    max_bytes = int(request.form.get("maxBytes", 25 * 1024 * 1024))
    upload = CloudinaryService.from_app().upload_file(
        request.files["file"],
        folder=folder,
        resource_type=resource_type,
        max_bytes=max_bytes,
    )
    return success_response({"asset": upload}, 201)


@cloudinary_bp.post("/delete")
@firebase_auth_required
def delete_assets():
    payload = request.get_json(silent=True) or {}
    public_ids = payload.get("publicIds") or []
    if isinstance(public_ids, str):
        public_ids = [public_ids]
    if not isinstance(public_ids, list) or not all(
        isinstance(item, str) for item in public_ids
    ):
        raise AppError("publicIds must be a list of strings.")
    resource_type = payload.get("resourceType", "image")
    deleted = CloudinaryService.from_app().delete_assets(
        public_ids,
        resource_type=resource_type,
    )
    return success_response({"deleted": deleted})
