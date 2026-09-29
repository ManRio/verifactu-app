from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderLineInput(BaseModel):
    product_id: int

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


class OrderCreate(BaseModel):
    business_id: int
    customer_id: int

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    lines: list[OrderLineInput] = Field(
        min_length=1,
    )


class OrderApiCreate(BaseModel):
    customer_id: int

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    lines: list[OrderLineInput] = Field(
        min_length=1,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class OrderUpdate(BaseModel):
    customer_id: int | None = None

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    lines: list[OrderLineInput] | None = Field(
        default=None,
        min_length=1,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class OrderLineRead(BaseModel):
    id: int
    order_id: int
    product_id: int

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


class OrderRead(BaseModel):
    id: int
    business_id: int
    customer_id: int

    status: str
    notes: str | None

    subtotal: Decimal
    tax_total: Decimal
    total_amount: Decimal

    created_at: datetime
    updated_at: datetime
    confirmed_at: datetime | None

    lines: list[OrderLineRead]

    model_config = ConfigDict(
        from_attributes=True,
    )