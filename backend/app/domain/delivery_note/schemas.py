from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DeliveryNoteLineInput(BaseModel):
    order_line_id: int

    quantity: Decimal = Field(
        gt=Decimal(0),
        max_digits=12,
        decimal_places=3,
    )

    position: int = Field(
        ge=1,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class DeliveryNoteCreate(BaseModel):
    business_id: int
    order_id: int
    delivery_date: date

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    lines: list[DeliveryNoteLineInput] = Field(
        min_length=1,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class DeliveryNoteApiCreate(BaseModel):
    order_id: int
    delivery_date: date

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    lines: list[DeliveryNoteLineInput] = Field(
        min_length=1,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class DeliveryNoteUpdate(BaseModel):
    delivery_date: date | None = None

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    lines: list[DeliveryNoteLineInput] | None = Field(
        default=None,
        min_length=1,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class DeliveryNoteLineRead(BaseModel):
    id: int
    delivery_note_id: int
    order_line_id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_rate: Decimal
    position: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class DeliveryNoteRead(BaseModel):
    id: int
    business_id: int
    order_id: int
    status: str
    delivery_date: date
    notes: str | None
    created_at: datetime
    updated_at: datetime
    confirmed_at: datetime | None
    lines: list[DeliveryNoteLineRead]

    model_config = ConfigDict(
        from_attributes=True,
    )