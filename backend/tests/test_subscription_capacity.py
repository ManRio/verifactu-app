"""Límites de trabajadores en los tres planes de demostración."""

from uuid import uuid4

import pytest

from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import BusinessService
from app.domain.subscription.quotas import (
    WorkerQuotaError,
    active_worker_count,
    validate_worker_slots,
)
from app.domain.subscription.service import SubscriptionService
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def _business(db):
    return BusinessService(db).create_business(BusinessCreate(
        legal_name="Empresa Quotas Demo", tax_id=f"CAP-{uuid4().hex[:12]}",
        address="Calle Inventada 1", postal_code="41001", city="Sevilla",
        province="Sevilla", country_code="ES",
    ))


def _worker(db, business_id):
    return UserService(db).create_user(UserCreate(
        business_id=business_id, email=f"user-{uuid4().hex[:12]}@example.com",
        password="password123", full_name="Trabajador Demo",
    ), role="WORKER")


def test_starter_has_no_worker_places(db_session):
    business = _business(db_session)
    owner = UserService(db_session).create_user(UserCreate(
        business_id=business.id, email=f"owner-{uuid4().hex[:12]}@example.com",
        password="password123", full_name="Propietario Demo",
    ), role="SUPERUSER")
    assert owner.role == "SUPERUSER"
    sub = SubscriptionService(db_session).demo_checkout(business.id, "STARTER")
    assert sub.max_workers == 0
    with pytest.raises(WorkerQuotaError):
        validate_worker_slots(db_session, business.id)
    db_session.rollback()


def test_pro_allows_five_workers_and_counts_invitations(db_session):
    business = _business(db_session)
    SubscriptionService(db_session).demo_checkout(business.id, "PRO")
    for _ in range(5):
        _worker(db_session, business.id)
    assert active_worker_count(db_session, business.id) == 5
    with pytest.raises(WorkerQuotaError):
        validate_worker_slots(db_session, business.id)
    db_session.rollback()


def test_downgrade_blocks_excess_worker_count(db_session):
    business = _business(db_session)
    service = SubscriptionService(db_session)
    service.demo_checkout(business.id, "BUSINESS")
    _worker(db_session, business.id)
    with pytest.raises(WorkerQuotaError):
        service.demo_checkout(business.id, "STARTER")
    # El error de cuota no invalida la transaccion.
    sub = service.get_read(business.id)
    assert sub is not None
    assert sub.plan_code == "BUSINESS"


def test_invitation_rejected_when_starter_has_zero_seats(client, db_session):
    business = _business(db_session)
    owner = UserService(db_session).create_user(UserCreate(
        business_id=business.id, email=f"owner-{uuid4().hex[:12]}@example.com",
        password="password123", full_name="Propietario Demo",
    ), role="SUPERUSER")
    SubscriptionService(db_session).demo_checkout(business.id, "STARTER")
    login = client.post("/auth/login", json={"email": owner.email, "password": "password123"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    result = client.post("/users", headers=headers, json={
        "email": f"worker-{uuid4().hex[:12]}@example.com", "full_name": "Nuevo trabajador",
    })
    assert result.status_code == 409
    assert active_worker_count(db_session, business.id) == 0
