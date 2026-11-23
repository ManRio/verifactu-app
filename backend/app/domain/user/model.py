from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    role: Mapped[str] = mapped_column(String(20), nullable=False, default="WORKER", server_default="WORKER")
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    must_set_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    verification_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True, unique=True)
    verification_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    business = relationship(
        "Business",
        back_populates="users",
    )

    __table_args__ = (
        CheckConstraint("role IN ('SUPERUSER', 'WORKER')", name="ck_users_role"),
        Index(
            "uq_users_email_lower",
            func.lower(email),
            unique=True,
        ),
    )