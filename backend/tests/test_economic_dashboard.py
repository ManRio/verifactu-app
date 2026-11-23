"""Cobertura del panel económico: período, seguridad y respuesta vacía."""

from uuid import uuid4

from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import BusinessService
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def _create_user(db, business_id, role):
    return UserService(db).create_user(UserCreate(
        business_id=business_id,
        email=f"dashboard-{uuid4().hex[:12]}@example.com",
        password="password123",
        full_name="Usuario Panel",
    ), role=role)


def _login(client, user):
    response = client.post("/auth/login", json={"email": user.email, "password": "password123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_summary_empty_month_and_superuser_access(client, db_session):
    business = BusinessService(db_session).create_business(BusinessCreate(
        legal_name="Dashboard Empresa", tax_id=f"DASH-{uuid4().hex[:12]}",
        address="Calle Demo 1", postal_code="41001", city="Sevilla",
        province="Sevilla", country_code="ES",
    ))
    owner = _create_user(db_session, business.id, "SUPERUSER")
    worker = _create_user(db_session, business.id, "WORKER")
    headers = _login(client, owner)
    response = client.get("/reports/summary?month=2026-11", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["period"] == "2026-11"
    assert body["total_invoiced"] == "0.00"
    assert body["cash_received_month"] == "0.00"
    assert body["outstanding_month_invoices"] == "0.00"
    assert len(body["trend"]) == 6
    assert body["top_products"] == []

    assert client.get("/reports/summary?month=2026-13", headers=headers).status_code == 422
    assert client.get("/reports/summary?month=2026-11", headers=_login(client, worker)).status_code == 403
