from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InvoiceCreate(BaseModel):
    business_id: int
    delivery_note_ids: list[int] = Field(
        min_length=1,
    )
    operation_date: date | None = None
    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class InvoiceApiCreate(BaseModel):
    delivery_note_ids: list[int] = Field(
        min_length=1,
    )
    operation_date: date | None = None
    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class InvoiceUpdate(BaseModel):
    delivery_note_ids: list[int] | None = Field(
        default=None,
        min_length=1,
    )
    operation_date: date | None = None
    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class InvoiceIssue(BaseModel):
    series_code: str = Field(
        default="F",
        min_length=1,
        max_length=20,
    )
    issue_date: date

    model_config = ConfigDict(
        extra="forbid",
    )


class InvoiceLineRead(BaseModel):
    id: int
    invoice_id: int
    delivery_note_line_id: int
    order_line_id: int

    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_rate: Decimal

    base_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal

    position: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class InvoiceDeliveryNoteRead(BaseModel):
    id: int
    invoice_id: int
    delivery_note_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class InvoiceRead(BaseModel):
    id: int
    business_id: int
    customer_id: int

    status: str
    invoice_type: str

    series: str | None
    number: int | None
    full_number: str | None

    issue_date: date | None
    operation_date: date | None

    issuer_legal_name: str
    issuer_tax_id: str
    issuer_address: str
    issuer_postal_code: str
    issuer_city: str
    issuer_province: str
    issuer_country_code: str

    customer_legal_name: str
    customer_tax_id: str | None
    customer_address: str | None
    customer_postal_code: str | None
    customer_city: str | None
    customer_province: str | None
    customer_country_code: str

    subtotal: Decimal
    tax_total: Decimal
    total_amount: Decimal

    notes: str | None

    created_at: datetime
    updated_at: datetime
    issued_at: datetime | None

    lines: list[InvoiceLineRead]
    delivery_notes: list[InvoiceDeliveryNoteRead]

    model_config = ConfigDict(
        from_attributes=True,
    )