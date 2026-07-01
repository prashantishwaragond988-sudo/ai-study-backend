import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    APP_NAME = os.getenv("APP_NAME", "AI Study App Backend")
    API_PREFIX = os.getenv("API_PREFIX", "/api")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Firebase Admin configuration.
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_CREDENTIALS_PATH = os.getenv(
        "FIREBASE_CREDENTIALS_PATH",
        str(BASE_DIR / "serviceAccountKey.json"),
    )

    # JWT configuration.
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"),
    )
    JWT_REFRESH_TOKEN_EXPIRES_DAYS = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30"),
    )

    # Future Cloudinary configuration.
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

    # Email configuration.
    EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "")
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

    # Future SMS and WhatsApp configuration.
    SMS_PROVIDER = os.getenv("SMS_PROVIDER", "")
    SMS_API_KEY = os.getenv("SMS_API_KEY", "")
    WHATSAPP_PROVIDER = os.getenv("WHATSAPP_PROVIDER", "")
    WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "")

    # Future AI provider configuration.
    AI_PROVIDER = os.getenv("AI_PROVIDER", "")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "")
