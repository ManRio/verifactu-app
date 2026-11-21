"""Movimientos de cobro con auditoría: no se eliminan ni editan importes."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"), nullable=False, index=True,
    )
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id"), nullable=False, index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="RECORDED", server_default="RECORDED",
    )
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False,
    )
    voided_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True,
    )
    void_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    voided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    invoice = relationship("Invoice")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        CheckConstraint("status IN ('RECORDED', 'VOIDED')", name="ck_payments_status"),
        CheckConstraint("method IN ('TRANSFER', 'CASH', 'CARD', 'OTHER')", name="ck_payments_method"),
        Index("ix_payments_business_invoice_status", "business_id", "invoice_id", "status"),
    )
