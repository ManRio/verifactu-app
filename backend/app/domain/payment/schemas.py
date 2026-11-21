"""Contratos API de cobros en EUR; el cliente nunca envía business_id."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PaymentMethod = Literal["TRANSFER", "CASH", "CARD", "OTHER"]
PaymentStatus = Literal["RECORDED", "VOIDED"]
BalanceStatus = Literal["UNPAID", "PARTIAL", "PAID"]


class PaymentCreate(BaseModel):
    invoice_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    payment_date: date
    method: PaymentMethod
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


class PaymentVoid(BaseModel):
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("reason", mode="before")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    model_config = ConfigDict(extra="forbid")


class PaymentRead(BaseModel):
    id: int
    business_id: int
    invoice_id: int
    amount: Decimal
    payment_date: date
    method: PaymentMethod
    reference: str | None
    notes: str | None
    status: PaymentStatus
    created_by_user_id: int
    voided_by_user_id: int | None
    void_reason: str | None
    created_at: datetime
    voided_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class InvoiceBalanceRead(BaseModel):
    invoice_id: int
    full_number: str
    customer_legal_name: str
    issue_date: date
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    payment_status: BalanceStatus


class InvoicePaymentsRead(BaseModel):
    balance: InvoiceBalanceRead
    payments: list[PaymentRead]
