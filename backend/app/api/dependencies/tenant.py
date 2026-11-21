from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.domain.subscription.service import SubscriptionService
from app.domain.user.model import User


def get_current_business_id(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> int:
    subscription = SubscriptionService(db).get_read(current_user.business_id)
    # Compatibilidad: las empresas anteriores a esta migración no tienen suscripción.
    if subscription is not None and subscription.status != "DEMO_ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Demo subscription required or expired",
        )
    return current_user.business_id
