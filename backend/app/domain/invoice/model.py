from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InvoiceSeries(Base):
    __tablename__ = "invoice_series"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    next_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
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

    business = relationship(
        "Business",
        back_populates="invoice_series",
    )

    invoices = relationship(
        "Invoice",
        back_populates="invoice_series",
    )

    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "code",
            name="uq_invoice_series_business_code",
        ),
    )


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    invoice_series_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoice_series.id"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
    )

    invoice_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="STANDARD",
        server_default="STANDARD",
    )

    series: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    full_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    issue_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    operation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    issuer_legal_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    issuer_tax_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    issuer_address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    issuer_postal_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    issuer_city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    issuer_province: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    issuer_country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )

    customer_legal_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    customer_tax_id: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    customer_address: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    customer_postal_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    customer_city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    customer_province: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    customer_country_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    tax_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
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

    issued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    business = relationship(
        "Business",
        back_populates="invoices",
    )

    customer = relationship(
        "Customer",
        back_populates="invoices",
    )

    invoice_series = relationship(
        "InvoiceSeries",
        back_populates="invoices",
    )

    lines = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLine.position",
    )

    delivery_notes = relationship(
        "InvoiceDeliveryNote",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "series",
            "number",
            name="uq_invoices_business_series_number",
        ),
        UniqueConstraint(
            "business_id",
            "full_number",
            name="uq_invoices_business_full_number",
        ),
        Index(
            "ix_invoices_business_status",
            "business_id",
            "status",
        ),
    )


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id"),
        nullable=False,
        index=True,
    )

    delivery_note_line_id: Mapped[int] = mapped_column(
        ForeignKey("delivery_note_lines.id"),
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

    base_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
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

    invoice = relationship(
        "Invoice",
        back_populates="lines",
    )

    delivery_note_line = relationship(
        "DeliveryNoteLine",
    )

    order_line = relationship(
        "OrderLine",
    )

    __table_args__ = (
        UniqueConstraint(
            "delivery_note_line_id",
            name="uq_invoice_lines_delivery_note_line_id",
        ),
    )


class InvoiceDeliveryNote(Base):
    __tablename__ = "invoice_delivery_notes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id"),
        nullable=False,
        index=True,
    )

    delivery_note_id: Mapped[int] = mapped_column(
        ForeignKey("delivery_notes.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    invoice = relationship(
        "Invoice",
        back_populates="delivery_notes",
    )

    delivery_note = relationship(
        "DeliveryNote",
        back_populates="invoice_links",
    )

    __table_args__ = (
        UniqueConstraint(
            "delivery_note_id",
            name="uq_invoice_delivery_notes_delivery_note_id",
        ),
        UniqueConstraint(
            "invoice_id",
            "delivery_note_id",
            name="uq_invoice_delivery_notes_invoice_delivery_note",
        ),
    )