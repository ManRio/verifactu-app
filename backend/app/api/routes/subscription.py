"""Endpoints de demostración comercial; no procesan pagos reales."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.domain.subscription.schemas import (
    DemoCheckoutRequest,
    DemoPlanRead,
    SubscriptionRead,
)
from app.domain.subscription.service import (
    DEMO_PLANS,
    InvalidDemoPlanError,
    SubscriptionService,
)
from app.domain.user.model import User

router = APIRouter(prefix="/subscriptions", tags=["subscriptions-demo"])


@router.get("/plans", response_model=list[DemoPlanRead])
def get_demo_plans() -> list[DemoPlanRead]:
    return list(DEMO_PLANS.values())


@router.get("/me", response_model=SubscriptionRead | None)
def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubscriptionRead | None:
    return SubscriptionService(db).get_read(current_user.business_id)


@router.post("/demo-checkout", response_model=SubscriptionRead)
def demo_checkout(
    payload: DemoCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubscriptionRead:
    try:
        return SubscriptionService(db).demo_checkout(current_user.business_id, payload.plan_code)
    except InvalidDemoPlanError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
