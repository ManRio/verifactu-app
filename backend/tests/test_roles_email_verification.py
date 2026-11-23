"""Regresión: permisos entre empresas y activación de correo de un solo uso."""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.auth.verification import (
    InvalidVerificationToken,
    VerificationService,
    token_digest,
)
from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import BusinessService
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def new_business(db: Session):
    return BusinessService(db).create_business(BusinessCreate(
        legal_name="Demo Roles", tax_id=f"ROL-{uuid.uuid4().hex[:12]}",
        address="Calle Prueba", postal_code="41001", city="Sevilla",
        province="Sevilla", country_code="ES",
    ))


def new_user(db: Session, business_id: int, email_verified: bool = True):
    return UserService(db).create_user(UserCreate(
        business_id=business_id, email=f"role-{uuid.uuid4().hex[:12]}@example.com",
        password="password123", full_name="Usuario de prueba",
    ), email_verified=email_verified)


def login(client: TestClient, user) -> dict[str, str]:
    r = client.post("/auth/login", json={"email": user.email, "password": "password123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_token_is_hashed_not_plaintext():
    assert token_digest("un-token") != "un-token"
    assert len(token_digest("un-token")) == 64


def test_activation_is_one_time_and_required_for_login(client: TestClient, db_session: Session):
    business = new_business(db_session)
    owner = new_user(db_session, business.id, email_verified=False)
    service = VerificationService(db_session)
    token = service.issue(owner)
    db_session.commit()
    assert owner.verification_token_hash != token
    r = client.post("/auth/login", json={"email": owner.email, "password": "password123"})
    assert r.status_code == 403
    r = client.post("/auth/verify-email", json={"token": token})
    assert r.status_code == 200
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 400
    assert client.post("/auth/login", json={"email": owner.email, "password": "password123"}).status_code == 200


def test_expired_token_is_rejected(db_session: Session):
    business = new_business(db_session)
    owner = new_user(db_session, business.id, email_verified=False)
    service = VerificationService(db_session)
    token = service.issue(owner)
    owner.verification_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()
    with pytest.raises(InvalidVerificationToken):
        service.confirm(token)


def test_worker_denied_user_routes_and_accounting_api(client: TestClient, db_session: Session):
    business = new_business(db_session)
    owner = new_user(db_session, business.id)
    worker = new_user(db_session, business.id)
    assert owner.role == "SUPERUSER"
    assert worker.role == "WORKER"
    headers = login(client, worker)
    assert client.get("/auth/me", headers=headers).json()["role"] == "WORKER"
    assert client.get("/users", headers=headers).status_code == 403
    assert client.post("/users", headers=headers, json={
        "email": f"new-{uuid.uuid4().hex[:12]}@example.com", "full_name": "Invitado"
    }).status_code == 403
    assert client.get("/reports/summary", headers=headers).status_code == 403
    assert client.post("/subscriptions/demo-checkout", headers=headers, json={"plan_code": "PRO"}).status_code == 403
    assert client.patch(f"/businesses/{business.id}", headers=headers, json={"trade_name": "Hack"}).status_code == 403


def test_owner_can_invite_worker_and_owner_sees_users(client: TestClient, db_session: Session):
    business = new_business(db_session)
    owner = new_user(db_session, business.id)
    headers = login(client, owner)
    assert client.get("/users", headers=headers).status_code == 200
    email = f"invite-{uuid.uuid4().hex[:12]}@example.com"
    result = client.post("/users", headers=headers, json={"email": email, "full_name": "Empleado"})
    assert result.status_code == 201
    body = result.json()
    assert body["role"] == "WORKER"
    assert body["email_verified"] is False
    assert "password" not in body and "password_hash" not in body
    user = UserService(db_session).get_by_email(email)
    assert user is not None and user.must_set_password is True


def test_worker_requires_new_password_on_invitation(db_session: Session):
    business = new_business(db_session)
    worker = new_user(db_session, business.id, email_verified=False)
    worker.must_set_password = True
    service = VerificationService(db_session)
    token = service.issue(worker)
    db_session.commit()
    with pytest.raises(InvalidVerificationToken):
        service.confirm(token)
    service.confirm(token, password="new-password123")
    assert UserService(db_session).authenticate_user(worker.email, "new-password123") is not None
