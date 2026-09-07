from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    business_id: int

    name: str = Field(
        min_length=1,
        max_length=150,
    )

    sku: str | None = Field(
        default=None,
        max_length=50,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    unit_price: Decimal = Field(
        ge=Decimal(0),
        max_digits=12,
        decimal_places=2,
    )

    tax_rate: Decimal = Field(
        ge=Decimal(0),
        le=Decimal(100),
        max_digits=5,
        decimal_places=2,
    )


class ProductApiCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
    )

    sku: str | None = Field(
        default=None,
        max_length=50,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    unit_price: Decimal = Field(
        ge=Decimal(0),
        max_digits=12,
        decimal_places=2,
    )

    tax_rate: Decimal = Field(
        ge=Decimal(0),
        le=Decimal(100),
        max_digits=5,
        decimal_places=2,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class ProductUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    sku: str | None = Field(
        default=None,
        max_length=50,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    unit_price: Decimal | None = Field(
        default=None,
        ge=Decimal(0),
        max_digits=12,
        decimal_places=2,
    )

    tax_rate: Decimal | None = Field(
        default=None,
        ge=Decimal(0),
        le=Decimal(100),
        max_digits=5,
        decimal_places=2,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class ProductRead(BaseModel):
    id: int
    business_id: int
    name: str
    sku: str | None
    description: str | None
    unit_price: Decimal
    tax_rate: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )