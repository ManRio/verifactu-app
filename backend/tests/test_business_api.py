from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import BusinessService
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def create_business(
    db_session: Session,
):
    service = BusinessService(db_session)

    return service.create_business(
        BusinessCreate(
            legal_name="Test Business API SL",
            tax_id=f"TEST-{uuid4().hex[:12]}",
            trade_name="Test API",
            address="Calle Prueba 123",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )


def get_auth_headers_for_business(
    client: TestClient,
    db_session: Session,
    business_id: int,
) -> dict[str, str]:
    email = (
        f"business-auth-{uuid4().hex[:12]}"
        "@example.com"
    )
    password = "password123"

    user_service = UserService(db_session)

    user_service.create_user(
        UserCreate(
            business_id=business_id,
            email=email,
            password=password,
            full_name="Business Auth User",
        )
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()[
        "access_token"
    ]

    return {
        "Authorization": f"Bearer {access_token}",
    }


def test_create_business_endpoint_is_not_exposed(
    client: TestClient,
):
    response = client.post(
        "/businesses",
        json={
            "legal_name": "Public Business SL",
            "tax_id": f"TEST-{uuid4().hex[:12]}",
            "address": "Calle Pública 1",
            "postal_code": "41001",
            "city": "Sevilla",
            "province": "Sevilla",
            "country_code": "ES",
        },
    )

    assert response.status_code == 405


def test_list_businesses_returns_only_authenticated_business(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(
        db_session,
    )
    other_business = create_business(
        db_session,
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    response = client.get(
        "/businesses",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["id"] == own_business.id
    assert body[0]["tax_id"] == own_business.tax_id

    returned_ids = {
        business["id"]
        for business in body
    }

    assert other_business.id not in returned_ids


def test_list_businesses_without_authentication_returns_401(
    client: TestClient,
):
    response = client.get(
        "/businesses",
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials"
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_own_business(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session,
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    response = client.get(
        f"/businesses/{business.id}",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == business.id
    assert body["legal_name"] == business.legal_name
    assert body["tax_id"] == business.tax_id
    assert body["trade_name"] == business.trade_name
    assert body["address"] == business.address
    assert body["postal_code"] == business.postal_code
    assert body["city"] == business.city
    assert body["province"] == business.province
    assert body["country_code"] == business.country_code


def test_get_other_business_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(
        db_session,
    )
    other_business = create_business(
        db_session,
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    response = client.get(
        f"/businesses/{other_business.id}",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource not found"
    }


def test_get_business_without_authentication_returns_401(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session,
    )

    response = client.get(
        f"/businesses/{business.id}",
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials"
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_update_own_business(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session,
    )

    original_tax_id = business.tax_id
    original_address = business.address
    original_postal_code = business.postal_code
    original_city = business.city
    original_province = business.province
    original_country_code = business.country_code

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    response = client.patch(
        f"/businesses/{business.id}",
        headers=headers,
        json={
            "legal_name": "Updated Business API SL",
            "trade_name": "Updated API",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == business.id
    assert body["legal_name"] == (
        "Updated Business API SL"
    )
    assert body["trade_name"] == "Updated API"

    assert body["tax_id"] == original_tax_id
    assert body["address"] == original_address
    assert body["postal_code"] == original_postal_code
    assert body["city"] == original_city
    assert body["province"] == original_province
    assert body["country_code"] == original_country_code


def test_update_other_business_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(
        db_session,
    )
    other_business = create_business(
        db_session,
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    response = client.patch(
        f"/businesses/{other_business.id}",
        headers=headers,
        json={
            "legal_name": "Forbidden Update SL",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource not found"
    }


def test_update_business_without_authentication_returns_401(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session,
    )

    response = client.patch(
        f"/businesses/{business.id}",
        json={
            "legal_name": "Unauthenticated Update SL",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials"
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_update_own_business_with_duplicate_tax_id_returns_409(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(
        db_session,
    )
    other_business = create_business(
        db_session,
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    response = client.patch(
        f"/businesses/{own_business.id}",
        headers=headers,
        json={
            "tax_id": other_business.tax_id,
        },
    )

    assert response.status_code == 409

    body = response.json()

    assert "detail" in body
    assert other_business.tax_id in body["detail"]


def test_deactivate_business_endpoint_is_not_exposed(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session,
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    response = client.patch(
        f"/businesses/{business.id}/deactivate",
        headers=headers,
    )

    assert response.status_code == 404


def test_activate_business_endpoint_is_not_exposed(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session,
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    response = client.patch(
        f"/businesses/{business.id}/activate",
        headers=headers,
    )

    assert response.status_code == 404

def test_update_business_rejects_is_active(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session,
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    response = client.patch(
        f"/businesses/{business.id}",
        headers=headers,
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 422