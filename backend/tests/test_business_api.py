from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def build_business_payload():
    return {
        "legal_name": "Test Business API SL",
        "tax_id": f"TEST-{uuid4().hex[:12]}",
        "trade_name": "Test API",
        "address": "Calle Prueba 123",
        "postal_code": "41001",
        "city": "Sevilla",
        "province": "Sevilla",
        "country_code": "ES",
    }


def get_auth_headers_for_business(
    client,
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

    access_token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {access_token}",
    }


def test_create_business(client):
    payload = build_business_payload()

    response = client.post(
        "/businesses",
        json=payload,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] is not None
    assert body["legal_name"] == payload["legal_name"]
    assert body["tax_id"] == payload["tax_id"]
    assert body["trade_name"] == payload["trade_name"]
    assert body["address"] == payload["address"]
    assert body["postal_code"] == payload["postal_code"]
    assert body["city"] == payload["city"]
    assert body["province"] == payload["province"]
    assert body["country_code"] == "ES"
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


def test_get_business(
    client,
    db_session: Session,
):
    payload = build_business_payload()

    create_response = client.post(
        "/businesses",
        json=payload,
    )

    assert create_response.status_code == 201

    created_business = create_response.json()
    business_id = created_business["id"]

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business_id,
    )

    response = client.get(
        f"/businesses/{business_id}",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == business_id
    assert body["legal_name"] == payload["legal_name"]
    assert body["tax_id"] == payload["tax_id"]
    assert body["trade_name"] == payload["trade_name"]
    assert body["address"] == payload["address"]
    assert body["postal_code"] == payload["postal_code"]
    assert body["city"] == payload["city"]
    assert body["province"] == payload["province"]
    assert body["country_code"] == payload["country_code"]


def test_duplicate_tax_id_returns_409(client):
    payload = build_business_payload()

    first_response = client.post(
        "/businesses",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/businesses",
        json=payload,
    )

    assert second_response.status_code == 409

    body = second_response.json()

    assert "detail" in body
    assert payload["tax_id"] in body["detail"]


def test_get_other_business_returns_404(
    client,
    db_session: Session,
):
    own_response = client.post(
        "/businesses",
        json=build_business_payload(),
    )

    other_response = client.post(
        "/businesses",
        json=build_business_payload(),
    )

    assert own_response.status_code == 201
    assert other_response.status_code == 201

    own_business_id = own_response.json()["id"]
    other_business_id = other_response.json()["id"]

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business_id,
    )

    response = client.get(
        f"/businesses/{other_business_id}",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource not found"
    }


def test_get_business_without_authentication_returns_401(
    client,
):
    response = client.get(
        "/businesses/1",
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials"
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_update_business(client):
    payload = build_business_payload()

    create_response = client.post(
        "/businesses",
        json=payload,
    )

    assert create_response.status_code == 201

    business_id = create_response.json()["id"]

    update_payload = {
        "legal_name": "Updated Business API SL",
        "trade_name": "Updated API",
    }

    response = client.patch(
        f"/businesses/{business_id}",
        json=update_payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == business_id
    assert body["legal_name"] == "Updated Business API SL"
    assert body["trade_name"] == "Updated API"

    # Los campos no enviados deben conservarse.
    assert body["tax_id"] == payload["tax_id"]
    assert body["address"] == payload["address"]
    assert body["postal_code"] == payload["postal_code"]
    assert body["city"] == payload["city"]
    assert body["province"] == payload["province"]
    assert body["country_code"] == payload["country_code"]


def test_update_nonexistent_business_returns_404(client):
    update_payload = {
        "legal_name": "Updated Business API SL",
    }

    response = client.patch(
        "/businesses/999999999",
        json=update_payload,
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Business not found."


def test_update_business_with_duplicate_tax_id_returns_409(
    client,
):
    first_payload = build_business_payload()
    second_payload = build_business_payload()

    first_response = client.post(
        "/businesses",
        json=first_payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/businesses",
        json=second_payload,
    )

    assert second_response.status_code == 201

    second_business_id = second_response.json()["id"]

    update_payload = {
        "tax_id": first_payload["tax_id"],
    }

    response = client.patch(
        f"/businesses/{second_business_id}",
        json=update_payload,
    )

    assert response.status_code == 409

    body = response.json()

    assert "detail" in body
    assert first_payload["tax_id"] in body["detail"]


def test_list_businesses(client):
    first_payload = build_business_payload()
    second_payload = build_business_payload()

    first_response = client.post(
        "/businesses",
        json=first_payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/businesses",
        json=second_payload,
    )

    assert second_response.status_code == 201

    response = client.get("/businesses")

    assert response.status_code == 200

    body = response.json()

    assert isinstance(body, list)

    business_ids = [
        business["id"]
        for business in body
    ]

    first_business_id = first_response.json()["id"]
    second_business_id = second_response.json()["id"]

    assert first_business_id in business_ids
    assert second_business_id in business_ids
    assert business_ids == sorted(business_ids)


def test_deactivate_business(client):
    payload = build_business_payload()

    create_response = client.post(
        "/businesses",
        json=payload,
    )

    assert create_response.status_code == 201

    business_id = create_response.json()["id"]

    response = client.patch(
        f"/businesses/{business_id}/deactivate",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == business_id
    assert body["is_active"] is False


def test_deactivate_nonexistent_business_returns_404(client):
    response = client.patch(
        "/businesses/999999999/deactivate",
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Business not found."


def test_activate_business(client):
    payload = build_business_payload()

    create_response = client.post(
        "/businesses",
        json=payload,
    )

    assert create_response.status_code == 201

    business_id = create_response.json()["id"]

    deactivate_response = client.patch(
        f"/businesses/{business_id}/deactivate",
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    response = client.patch(
        f"/businesses/{business_id}/activate",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == business_id
    assert body["is_active"] is True


def test_activate_nonexistent_business_returns_404(client):
    response = client.patch(
        "/businesses/999999999/activate",
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Business not found."