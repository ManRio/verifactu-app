from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DeliveryNote(Base):
    __tablename__ = "delivery_notes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
    )

    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

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

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    business = relationship(
        "Business",
        back_populates="delivery_notes",
    )

    order = relationship(
        "Order",
        back_populates="delivery_notes",
    )

    lines = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        order_by="DeliveryNoteLine.position",
    )

    invoice_links = relationship(
        "InvoiceDeliveryNote",
        back_populates="delivery_note",
    )


class DeliveryNoteLine(Base):
    __tablename__ = "delivery_note_lines"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    delivery_note_id: Mapped[int] = mapped_column(
        ForeignKey("delivery_notes.id"),
        nullable=False,
        index=True,
    )

    order_line_id: Mapped[int] = mapped_column(
        ForeignKey("order_lines.id"),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    delivery_note = relationship(
        "DeliveryNote",
        back_populates="lines",
    )

    order_line = relationship(
        "OrderLine",
        back_populates="delivery_note_lines",
    )