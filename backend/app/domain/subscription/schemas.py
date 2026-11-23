"""Contratos HTTP para la suscripción simulada."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DemoPlanRead(BaseModel):
    code: str
    name: str
    monthly_price_eur: str
    features: list[str]
    max_workers: int = 0


class DemoCheckoutRequest(BaseModel):
    plan_code: str = Field(min_length=1, max_length=20)
    model_config = ConfigDict(extra="forbid")


class SubscriptionRead(BaseModel):
    status: str
    plan_code: str | None
    plan_name: str | None
    monthly_price_eur: str | None
    activated_at: datetime | None
    period_end: datetime | None
    is_demo: bool = True
    payment_collected: bool = False
    max_workers: int = 0
    active_workers: int = 0
    available_workers: int = 0
