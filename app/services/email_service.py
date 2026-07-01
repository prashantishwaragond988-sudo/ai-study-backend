import logging

import resend
from flask import Flask

from app.common.errors import AppError

logger = logging.getLogger(__name__)


class ResendEmailService:
    """Resend email delivery service."""

    def __init__(
        self,
        api_key: str,
        sender: str,
    ):
        self.api_key = api_key
        self.sender = sender

    @classmethod
    def from_app(cls, app: Flask) -> "ResendEmailService":
        return cls(
            api_key=app.config["RESEND_API_KEY"],
            sender=app.config["EMAIL_FROM"],
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.sender)

    def send_registration_otp(self, *, name: str, email: str, otp: str) -> None:
        subject = "AI Study App Email Verification"
        html = (
            f"<p>Hello {name},</p>"
            "<p>Your verification code is:</p>"
            f"<h2>{otp}</h2>"
            "<p>This code expires in 5 minutes.</p>"
        )
        self.send_email(to_email=email, subject=subject, html=html)

    def send_email(self, *, to_email: str, subject: str, html: str) -> None:
        if not self.is_configured:
            raise AppError(
                "Email service is not configured. Set RESEND_API_KEY and EMAIL_FROM.",
                503,
            )

        try:
            resend.api_key = self.api_key
            resend.Emails.send(
                {
                    "from": self.sender,
                    "to": [to_email],
                    "subject": subject,
                    "html": html,
                }
            )
            logger.info("Sent registration OTP email to %s.", to_email)
        except Exception as error:
            logger.exception("Resend email delivery failed for %s.", to_email)
            raise AppError("Could not send verification email.", 500) from error


EmailService = ResendEmailService
