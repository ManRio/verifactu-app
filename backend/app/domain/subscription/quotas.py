"""Aforo de trabajadores por empresa (planes únicamente simulados)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.subscription.model import Subscription
from app.domain.user.model import User

# STARTER: 1 superusuario y 0 trabajadores; PRO: 1+5; BUSINESS: 1+10.
WORKER_CAPS: dict[str, int] = {"STARTER": 0, "PRO": 5, "BUSINESS": 10}


class WorkerQuotaError(ValueError):
    pass


def active_worker_count(db: Session, business_id: int) -> int:
    """Incluye invitaciones pendientes activas para evitar sobreasignar plazas."""
    return int(db.scalar(select(func.count(User.id)).where(
        User.business_id == business_id,
        User.role == "WORKER",
        User.is_active.is_(True),
    )) or 0)


def validate_worker_slots(db: Session, business_id: int) -> None:
    """Bloquea la fila del plan hasta el commit que crea/activa un trabajador."""
    sub = db.scalar(
        select(Subscription)
        .where(Subscription.business_id == business_id)
        .with_for_update()
    )
    if sub is None:
        # Empresas antiguas sin ficha de suscripción: compatibilidad temporal.
        cap = 5
    else:
        if sub.status != "DEMO_ACTIVE" or sub.plan_code not in WORKER_CAPS:
            raise WorkerQuotaError("Activa un plan de demostración antes de invitar trabajadores")

        from datetime import UTC, datetime

        if sub.period_end is None or sub.period_end <= datetime.now(UTC):
            raise WorkerQuotaError("El plan de demostración ha caducado")
        cap = WORKER_CAPS[sub.plan_code]
    used = active_worker_count(db, business_id)
    if used >= cap:
        raise WorkerQuotaError(
            f"El plan permite {cap} trabajadores. "
            "Desactiva uno o cambia a un plan superior."
        )


def validate_plan_change(db: Session, business_id: int, plan_code: str) -> None:
    used = active_worker_count(db, business_id)
    cap = WORKER_CAPS[plan_code]
    if used > cap:
        raise WorkerQuotaError(
            f"No puedes cambiar a este plan: tienes {used} trabajadores activos "
            f"o invitados y el límite es {cap}. Desactiva trabajadores primero."
        )
