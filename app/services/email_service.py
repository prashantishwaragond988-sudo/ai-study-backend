import logging
import smtplib
from email.message import EmailMessage

from flask import Flask

from app.common.errors import AppError

logger = logging.getLogger(__name__)


class EmailService:
    """SMTP email delivery service."""

    def __init__(
        self,
        provider: str,
        sender: str,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
    ):
        self.provider = provider
        self.sender = sender
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password

    @classmethod
    def from_app(cls, app: Flask) -> "EmailService":
        return cls(
            provider=app.config["EMAIL_PROVIDER"],
            sender=app.config["EMAIL_FROM"],
            smtp_host=app.config["SMTP_HOST"],
            smtp_port=app.config["SMTP_PORT"],
            smtp_username=app.config["SMTP_USERNAME"],
            smtp_password=app.config["SMTP_PASSWORD"],
        )

    @property
    def is_configured(self) -> bool:
        return bool(
            self.sender
            and self.smtp_host
            and self.smtp_port
            and self.smtp_username
            and self.smtp_password
        )

    def send_registration_otp(self, *, name: str, email: str, otp: str) -> None:
        subject = "AI Study App Email Verification"
        body = (
            f"Hello {name},\n\n"
            "Your verification code is:\n\n"
            f"{otp}\n\n"
            "This code expires in 5 minutes."
        )
        self.send_email(to_email=email, subject=subject, body=body)

    def send_email(self, *, to_email: str, subject: str, body: str) -> None:
        if not self.is_configured:
            raise AppError(
                "Email service is not configured. Set Gmail SMTP values in .env.",
                503,
            )

        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as smtp:
                smtp.starttls()
                smtp.login(self.smtp_username, self.smtp_password)
                smtp.send_message(message)
            logger.info("Sent registration OTP email to %s.", to_email)
        except smtplib.SMTPException as error:
            logger.exception("SMTP email delivery failed for %s.", to_email)
            raise AppError("Could not send verification email.", 502) from error
