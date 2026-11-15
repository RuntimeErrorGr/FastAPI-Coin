import smtplib
from email.message import EmailMessage

from app.config import settings


class EmailSender:
    """Sends plain-text emails through an SMTP server."""

    def __init__(
        self,
        host: str,
        port: int,
        sender: str,
        username: str | None = None,
        password: str | None = None,
        starttls: bool = False,
    ):
        self._host = host
        self._port = port
        self._sender = sender
        self._username = username
        self._password = password
        self._starttls = starttls

    def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self._host, self._port, timeout=10) as smtp:
            if self._starttls:
                smtp.starttls()
            if self._username:
                smtp.login(self._username, self._password or "")
            smtp.send_message(message)


def create_email_sender() -> EmailSender:
    """Creates the sender from the SMTP_* settings."""
    return EmailSender(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        sender=settings.EMAIL_FROM,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        starttls=settings.SMTP_STARTTLS,
    )
