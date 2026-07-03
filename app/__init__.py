import logging

from flask_cors import CORS
from flask import Flask

from app.common.errors import register_error_handlers
from app.auth.routes import auth_bp
from app.cloudinary_routes.routes import cloudinary_bp
from app.config import Config
from app.firestore.routes import firestore_bp
from app.health.routes import health_bp
from app.services.cloudinary_service import CloudinaryService
from app.services.firebase_admin_service import FirebaseAdminService


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    _configure_logging()
    CORS(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})
    FirebaseAdminService.from_app(app).initialize()
    with app.app_context():
        CloudinaryService.from_app().verify_connection()

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cloudinary_bp)
    app.register_blueprint(firestore_bp)
    register_error_handlers(app)

    return app


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
