from flask import Blueprint, current_app
import firebase_admin

from app.services.cloudinary_service import CloudinaryService

health_bp = Blueprint("health", __name__)


@health_bp.get("/")
def root_check():
    return {
        "app": "AI Study Backend",
        "status": "running",
        "version": "1.0",
    }


@health_bp.get("/health")
def health_check():
    cloudinary_service = CloudinaryService.from_app()
    cloudinary_service.verify_connection()
    return {
        "status": "healthy",
        "firebase": "connected" if firebase_admin._apps else "disconnected",
        "cloudinary": "connected",
    }


@health_bp.get("/deployment")
def deployment_check():
    cloudinary_service = CloudinaryService.from_app()
    return {
        "app": current_app.config["APP_NAME"],
        "environment": current_app.config["FLASK_ENV"],
        "firebaseConfigured": bool(firebase_admin._apps),
        "cloudinaryEnvironment": cloudinary_service.verify_environment(),
    }
