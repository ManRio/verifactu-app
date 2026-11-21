"""Activación y consulta de planes de demostración, sin pasarela de pago."""
from calendar import monthrange
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.subscription.model import Subscription
from app.domain.subscription.schemas import DemoPlanRead, SubscriptionRead

DEMO_PLANS = {
    "STARTER": DemoPlanRead(
        code="STARTER",
        name="Inicio",
        monthly_price_eur="12.90",
        features=["Clientes y productos", "Pedidos y albaranes", "Facturas de prueba"],
    ),
    "PRO": DemoPlanRead(
        code="PRO",
        name="Profesional",
        monthly_price_eur="24.90",
        features=["Todas las funciones actuales", "Organización multiusuario (API)",
                  "Funciones adicionales en desarrollo"],
    ),
}


class InvalidDemoPlanError(ValueError):
    pass


def add_calendar_month(value: datetime) -> datetime:
    """Conserva día/hora, ajustando días inexistentes al último del mes."""
    year = value.year + (value.month // 12)
    month = (value.month % 12) + 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def get_model(self, business_id: int) -> Subscription | None:
        return self.db.scalar(
            select(Subscription).where(Subscription.business_id == business_id)
        )

    def get_read(self, business_id: int) -> SubscriptionRead | None:
        subscription = self.get_model(business_id)
        if subscription is None:
            return None  # Negocios previos a la introducción de suscripciones.

        plan = DEMO_PLANS.get(subscription.plan_code or "")
        is_expired = (
            subscription.status == "DEMO_ACTIVE"
            and (subscription.period_end is None or subscription.period_end <= datetime.now(UTC))
        )
        return SubscriptionRead(
            status="DEMO_EXPIRED" if is_expired else subscription.status,
            plan_code=subscription.plan_code,
            plan_name=plan.name if plan else None,
            monthly_price_eur=plan.monthly_price_eur if plan else None,
            activated_at=subscription.activated_at,
            period_end=subscription.period_end,
        )

    def demo_checkout(self, business_id: int, plan_code: str) -> SubscriptionRead:
        if plan_code not in DEMO_PLANS:
            raise InvalidDemoPlanError("Plan de demostración no válido")

        subscription = self.get_model(business_id)
        if subscription is None:
            subscription = Subscription(business_id=business_id)
            self.db.add(subscription)

        # Simulamos la contratación y su siguiente fecha mensual, no un cobro.
        now = datetime.now(UTC)
        subscription.status = "DEMO_ACTIVE"
        subscription.plan_code = plan_code
        subscription.activated_at = now
        subscription.period_end = add_calendar_month(now)
        self.db.commit()
        result = self.get_read(business_id)
        assert result is not None
        return result
