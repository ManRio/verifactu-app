"""Correo de confirmación: SMTP real o consola SOLO en desarrollo."""
import logging
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailDeliveryUnavailable(RuntimeError):
    pass


def ensure_email_ready() -> None:
    mode = settings.email_backend.lower()
    if mode == "console" and settings.app_environment != "development":
        raise EmailDeliveryUnavailable("La consola solo está permitida en desarrollo")
    if mode == "smtp" and (not settings.smtp_host or not settings.smtp_from):
        raise EmailDeliveryUnavailable("Falta configurar SMTP_HOST y SMTP_FROM")
    if mode not in {"smtp", "console"}:
        raise EmailDeliveryUnavailable("EMAIL_BACKEND debe ser smtp o console")


def send_activation_email(email: str, name: str, token: str, *, employee: bool) -> None:
    ensure_email_ready()
    url = settings.frontend_base_url.rstrip("/") + "/verify-email?" + urlencode({"token": token, **({"type": "worker"} if employee else {})})
    subject = "Activa tu acceso a VeriFactu App"
    instructions = (
        "Has sido invitado como trabajador. Abre el enlace y elige tu contraseña."
        if employee else "Gracias por registrarte. Abre el enlace para confirmar tu correo."
    )
    message = f"Hola {name},\n\n{instructions}\n\n{url}\n\nEl enlace caduca en 24 horas y solo se puede utilizar una vez.\nSi no esperabas este mensaje, puedes ignorarlo.\n"

    if settings.email_backend.lower() == "console":
        logger.warning("ACTIVACIÓN DESARROLLO para %s: %s", email, url)
        return

    mail = EmailMessage()
    mail["From"] = settings.smtp_from
    mail["To"] = email
    mail["Subject"] = subject
    mail.set_content(message)
    try:
        if settings.smtp_ssl:
            client = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10, context=ssl.create_default_context())
        else:
            client = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
        with client:
            if not settings.smtp_ssl and settings.smtp_starttls:
                client.starttls(context=ssl.create_default_context())
            if settings.smtp_user:
                client.login(settings.smtp_user, settings.smtp_password)
            client.send_message(mail)
    except (OSError, smtplib.SMTPException) as exc:
        logger.exception("No se pudo enviar el correo de activación")
        raise EmailDeliveryUnavailable("No se pudo enviar el correo de activación") from exc
