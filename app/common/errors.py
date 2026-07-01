import logging

from flask import Flask, jsonify

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        payload = {"ok": False, "error": error.message}
        if error.details:
            payload["details"] = error.details
        return jsonify(payload), error.status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({"ok": False, "error": "Endpoint not found."}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        logger.exception("Unhandled backend error: %s", error)
        return jsonify({"ok": False, "error": "Internal server error."}), 500
