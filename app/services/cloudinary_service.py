import logging
import mimetypes
from tempfile import NamedTemporaryFile

import cloudinary
import cloudinary.api
import cloudinary.uploader
from flask import current_app

from app.common.errors import AppError

logger = logging.getLogger(__name__)


class CloudinaryService:
    """Reusable Cloudinary upload and deletion helper."""

    allowed_image_types = {"image/jpeg", "image/png", "image/webp", "image/heic"}
    allowed_pdf_types = {"application/pdf"}
    allowed_raw_types = {
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        if self.is_configured:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True,
            )

    @classmethod
    def from_app(cls) -> "CloudinaryService":
        return cls(
            current_app.config["CLOUDINARY_CLOUD_NAME"],
            current_app.config["CLOUDINARY_API_KEY"],
            current_app.config["CLOUDINARY_API_SECRET"],
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.cloud_name and self.api_key and self.api_secret)

    def verify_environment(self) -> dict[str, bool]:
        return {
            "CLOUDINARY_CLOUD_NAME": bool(self.cloud_name),
            "CLOUDINARY_API_KEY": bool(self.api_key),
            "CLOUDINARY_API_SECRET": bool(self.api_secret),
        }

    def verify_connection(self) -> bool:
        self._ensure_configured()
        try:
            cloudinary.api.ping()
        except Exception as error:
            logger.exception("Cloudinary connection check failed: %s", error)
            raise AppError("Cloudinary is not connected.", 503) from error
        return True

    def upload_file(
        self,
        file_storage,
        *,
        folder: str,
        resource_type: str,
        max_bytes: int,
    ) -> dict:
        self._ensure_configured()
        self._validate_folder(folder)
        self._validate_resource_type(resource_type)
        content_type = file_storage.mimetype or mimetypes.guess_type(
            file_storage.filename,
        )[0]
        self._validate_content_type(content_type, resource_type)

        file_bytes = file_storage.read()
        if len(file_bytes) > max_bytes:
            raise AppError("File is too large.", 413)

        try:
            result = cloudinary.uploader.upload(
                file_bytes,
                folder=folder,
                resource_type=resource_type,
                use_filename=True,
                unique_filename=True,
                overwrite=False,
            )
        except Exception as error:
            logger.exception("Cloudinary upload failed: %s", error)
            raise AppError("Cloudinary upload failed.", 502) from error

        logger.info(
            "Uploaded Cloudinary asset public_id=%s resource_type=%s folder=%s",
            result.get("public_id"),
            resource_type,
            folder,
        )
        return {
            "secureUrl": result["secure_url"],
            "publicId": result["public_id"],
            "resourceType": result.get("resource_type", resource_type),
        }

    def delete_asset(self, public_id: str, *, resource_type: str = "image") -> dict:
        self._ensure_configured()
        self._validate_resource_type(resource_type)
        if not public_id or not isinstance(public_id, str):
            raise AppError("A valid publicId is required.")
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        except Exception as error:
            logger.exception("Cloudinary delete failed for %s: %s", public_id, error)
            raise AppError("Cloudinary delete failed.", 502) from error
        logger.info("Deleted Cloudinary asset public_id=%s result=%s", public_id, result)
        return result

    def delete_assets(
        self,
        public_ids: list[str],
        *,
        resource_type: str = "image",
    ) -> list[dict]:
        return [
            {
                "publicId": public_id,
                "result": self.delete_asset(public_id, resource_type=resource_type),
            }
            for public_id in public_ids
        ]

    def _ensure_configured(self) -> None:
        if not self.is_configured:
            raise AppError("Cloudinary is not configured on the backend.", 500)

    def _validate_content_type(
        self,
        content_type: str | None,
        resource_type: str,
    ) -> None:
        allowed = {
            "image": self.allowed_image_types,
            "raw": self.allowed_raw_types,
            "auto": self.allowed_image_types | self.allowed_raw_types,
        }[resource_type]
        if not content_type or content_type not in allowed:
            raise AppError("Unsupported file type.", 415)

    def _validate_resource_type(self, resource_type: str) -> None:
        if resource_type not in {"image", "raw", "auto"}:
            raise AppError("Unsupported Cloudinary resource type.")

    def _validate_folder(self, folder: str) -> None:
        if not folder or ".." in folder or folder.startswith("/"):
            raise AppError("Invalid Cloudinary folder.")
