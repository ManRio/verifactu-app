"""Tokens aleatorios con hash persistido, expiración y consumo único."""
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.domain.user.model import User


class InvalidVerificationToken(ValueError):
    pass


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class VerificationService:
    def __init__(self, db: Session):
        self.db = db

    def issue(self, user: User) -> str:
        token = secrets.token_urlsafe(40)
        user.verification_token_hash = token_digest(token)
        user.verification_expires_at = datetime.now(UTC) + timedelta(hours=24)
        user.verification_sent_at = datetime.now(UTC)
        self.db.flush()
        return token

    def confirm(self, token: str, password: str | None = None) -> User:
        if not token or len(token) > 200:
            raise InvalidVerificationToken("Enlace de verificación inválido")
        user = self.db.scalar(
            select(User).where(User.verification_token_hash == token_digest(token)).with_for_update()
        )
        now = datetime.now(UTC)
        if user is None or user.email_verified or user.verification_expires_at is None:
            raise InvalidVerificationToken("Enlace no válido o ya utilizado")
        expires = user.verification_expires_at
        if (expires.replace(tzinfo=UTC) if expires.tzinfo is None else expires) <= now:
            raise InvalidVerificationToken("El enlace de activación ha caducado")
        if user.must_set_password:
            if not password or not 8 <= len(password) <= 128:
                raise InvalidVerificationToken("Debes establecer una contraseña de al menos 8 caracteres")
            user.password_hash = hash_password(password)
            user.must_set_password = False
        user.email_verified = True
        user.verification_token_hash = None
        user.verification_expires_at = None
        self.db.commit()
        return user

    def resend(self, user: User) -> str | None:
        if user.email_verified:
            return None
        now = datetime.now(UTC)
        sent = user.verification_sent_at
        if sent is not None and (now - (sent.replace(tzinfo=UTC) if sent.tzinfo is None else sent)).total_seconds() < 60:
            return None
        token = self.issue(user)
        self.db.commit()
        return token
