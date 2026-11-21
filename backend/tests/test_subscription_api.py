"""Pruebas API de onboarding y suscripciones simuladas."""
from uuid import uuid4


def make_registration():
    unique = uuid4().hex[:14]
    return {
        "business": {
            "legal_name": "Demo SaaS Business SL",
            "tax_id": f"TEST-{unique}",
            "address": "Calle Demo 1",
            "postal_code": "41001",
            "city": "Sevilla",
            "province": "Sevilla",
            "country_code": "ES",
        },
        "user": {
            "email": f"saas-{unique}@example.com",
            "password": "password123",
            "full_name": "Usuario Demo",
        },
    }


def register(client):
    response = client.post("/auth/register", json=make_registration())
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_demo_plans_are_public(client):
    response = client.get("/subscriptions/plans")
    assert response.status_code == 200
    assert {plan["code"] for plan in response.json()} == {"STARTER", "PRO"}


def test_signup_creates_pending_subscription(client):
    headers = register(client)
    response = client.get("/subscriptions/me", headers=headers)
    assert response.status_code == 200
    subscription = response.json()
    assert subscription["status"] == "PENDING"
    assert subscription["plan_code"] is None
    assert subscription["payment_collected"] is False
    # El resto de la API queda bloqueado hasta activar el demo.
    denied = client.get("/products", headers=headers)
    assert denied.status_code == 402


def test_checkout_activates_simulated_monthly_plan(client):
    headers = register(client)
    response = client.post(
        "/subscriptions/demo-checkout", headers=headers,
        json={"plan_code": "STARTER"},
    )
    assert response.status_code == 200
    subscription = response.json()
    assert subscription["status"] == "DEMO_ACTIVE"
    assert subscription["plan_code"] == "STARTER"
    assert subscription["monthly_price_eur"] == "12.90"
    assert subscription["period_end"] is not None
    assert subscription["payment_collected"] is False
    fetched = client.get("/subscriptions/me", headers=headers)
    assert fetched.json()["plan_code"] == "STARTER"
    assert client.get("/products", headers=headers).status_code == 200


def test_invalid_plan_does_not_activate_subscription(client):
    headers = register(client)
    response = client.post(
        "/subscriptions/demo-checkout", headers=headers,
        json={"plan_code": "FREE_FOREVER"},
    )
    assert response.status_code == 422
    assert client.get("/subscriptions/me", headers=headers).json()["status"] == "PENDING"


def test_subscription_is_scoped_to_current_business(client):
    first_headers = register(client)
    second_headers = register(client)
    first = client.post(
        "/subscriptions/demo-checkout", headers=first_headers,
        json={"plan_code": "PRO"},
    )
    assert first.status_code == 200
    own = client.get("/subscriptions/me", headers=second_headers)
    assert own.status_code == 200
    assert own.json()["status"] == "PENDING"
    assert own.json()["plan_code"] is None


def test_subscription_endpoint_requires_login(client):
    response = client.get("/subscriptions/me")
    assert response.status_code == 401


def test_expired_demo_blocks_api_but_allows_renewal(client, db_session):
    from datetime import UTC, datetime, timedelta

    from app.domain.subscription.model import Subscription

    headers = register(client)
    response = client.post(
        "/subscriptions/demo-checkout", headers=headers,
        json={"plan_code": "STARTER"},
    )
    assert response.status_code == 200

    subscription = db_session.query(Subscription).order_by(Subscription.id.desc()).first()
    assert subscription is not None
    subscription.period_end = datetime.now(UTC) - timedelta(days=1)
    db_session.flush()

    assert client.get("/subscriptions/me", headers=headers).json()["status"] == "DEMO_EXPIRED"
    assert client.get("/products", headers=headers).status_code == 402
    renewed = client.post(
        "/subscriptions/demo-checkout", headers=headers,
        json={"plan_code": "PRO"},
    )
    assert renewed.status_code == 200
    assert renewed.json()["status"] == "DEMO_ACTIVE"
    assert client.get("/products", headers=headers).status_code == 200
