import logging
import smtplib
from email.message import EmailMessage

from modules.utils.config import settings

logger = logging.getLogger(__name__)


def _create_smtp_client() -> smtplib.SMTP:
    if settings.SMTP_USE_SSL:
        return smtplib.SMTP_SSL(
            settings.SMTP_HOST, settings.SMTP_PORT, timeout=10
        )

    client = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)

    if settings.SMTP_USE_TLS:
        client.starttls()

    return client


def _send_email(recipient: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    try:
        with _create_smtp_client() as smtp:
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

            smtp.send_message(message)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Не удалось отправить письмо с кодом подтверждения")
        raise RuntimeError(
            "Не удалось отправить письмо с кодом подтверждения"
        ) from exc


def send_password_reset_code(recipient: str, code: str) -> None:
    subject = "Код для восстановления пароля"
    body = (
        "Мы получили запрос на смену пароля.\n\n"
        f"Код подтверждения: {code}\n\n"
        "Если вы не запрашивали смену пароля, просто игнорируйте это письмо."
    )
    _send_email(recipient, subject, body)