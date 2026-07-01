from datetime import datetime, timezone

from flask import Blueprint, current_app

from app.common.responses import success_response

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    return success_response(
        {
            "status": "running",
            "service": current_app.config["APP_NAME"],
            "environment": current_app.config["FLASK_ENV"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
