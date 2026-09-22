from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreate(BaseModel):
    business_id: int

    tax_id: str | None = Field(
        default=None,
        max_length=20,
    )

    legal_name: str = Field(
        min_length=1,
        max_length=150,
    )

    trade_name: str | None = Field(
        default=None,
        max_length=150,
    )

    address: str | None = Field(
        default=None,
        max_length=250,
    )

    postal_code: str | None = Field(
        default=None,
        max_length=10,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    province: str | None = Field(
        default=None,
        max_length=100,
    )

    country_code: str = Field(
        default="ES",
        min_length=2,
        max_length=2,
    )

    email: str | None = Field(
        default=None,
        max_length=254,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )


class CustomerApiCreate(BaseModel):
    tax_id: str | None = Field(
        default=None,
        max_length=20,
    )

    legal_name: str = Field(
        min_length=1,
        max_length=150,
    )

    trade_name: str | None = Field(
        default=None,
        max_length=150,
    )

    address: str | None = Field(
        default=None,
        max_length=250,
    )

    postal_code: str | None = Field(
        default=None,
        max_length=10,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    province: str | None = Field(
        default=None,
        max_length=100,
    )

    country_code: str = Field(
        default="ES",
        min_length=2,
        max_length=2,
    )

    email: str | None = Field(
        default=None,
        max_length=254,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class CustomerUpdate(BaseModel):
    tax_id: str | None = Field(
        default=None,
        max_length=20,
    )

    legal_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    trade_name: str | None = Field(
        default=None,
        max_length=150,
    )

    address: str | None = Field(
        default=None,
        max_length=250,
    )

    postal_code: str | None = Field(
        default=None,
        max_length=10,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    province: str | None = Field(
        default=None,
        max_length=100,
    )

    country_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
    )

    email: str | None = Field(
        default=None,
        max_length=254,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class CustomerRead(BaseModel):
    id: int
    business_id: int
    tax_id: str | None
    legal_name: str
    trade_name: str | None
    address: str | None
    postal_code: str | None
    city: str | None
    province: str | None
    country_code: str
    email: str | None
    phone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )