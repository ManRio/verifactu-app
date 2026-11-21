
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.tenant import get_current_business_id
from app.domain.subscription.model import Subscription
from app.domain.user.model import User


def make_user() -> User:
    return User(
        business_id=42,
        email="tenant@example.com",
        password_hash="hashed-password",
        full_name="Tenant User",
    )


def make_db(subscription: Subscription | None) -> Session:
    db = Mock(spec=Session)
    db.scalar.return_value = subscription
    return db


def test_get_current_business_id_returns_user_business_id():
    """Los negocios anteriores sin suscripción conservan acceso."""
    business_id = get_current_business_id(
        current_user=make_user(),
        db=make_db(None),
    )

    assert business_id == 42


def test_pending_subscription_blocks_business_access():
    """Una empresa nueva debe activar el plan de demostración."""
    subscription = Subscription(
        business_id=42,
        status="PENDING",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_business_id(
            current_user=make_user(),
            db=make_db(subscription),
        )

    assert exc_info.value.status_code == 402


def test_active_subscription_allows_business_access():
    """Un plan de demostración activo permite acceder."""
    now = datetime.now(UTC)

    subscription = Subscription(
        business_id=42,
        status="DEMO_ACTIVE",
        plan_code="STARTER",
        activated_at=now,
        period_end=now + timedelta(days=30),
    )

    business_id = get_current_business_id(
        current_user=make_user(),
        db=make_db(subscription),
    )

    assert business_id == 42
