import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate


def test_create_user(
    client: TestClient,
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="User API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle API 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    email = f"user-{uuid.uuid4().hex[:12]}@example.com"

    response = client.post(
        "/users",
        json={
            "business_id": business.id,
            "email": email,
            "password": "password123",
            "full_name": "API User",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["business_id"] == business.id
    assert data["email"] == email
    assert data["full_name"] == "API User"
    assert data["is_active"] is True

    assert "password" not in data
    assert "password_hash" not in data

def test_get_user(
    client: TestClient,
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Get User API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle API 2",
            postal_code="41002",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    create_response = client.post(
        "/users",
        json={
            "business_id": business.id,
            "email": f"user-{uuid.uuid4().hex[:12]}@example.com",
            "password": "password123",
            "full_name": "Get API User",
        },
    )

    user_id = create_response.json()["id"]

    response = client.get(f"/users/{user_id}")

    assert response.status_code == 200
    assert response.json()["id"] == user_id


def test_get_user_returns_404_when_not_found(
    client: TestClient,
):
    response = client.get("/users/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_user(
    client: TestClient,
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Update User API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle API 3",
            postal_code="41003",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    create_response = client.post(
        "/users",
        json={
            "business_id": business.id,
            "email": f"user-{uuid.uuid4().hex[:12]}@example.com",
            "password": "password123",
            "full_name": "Original API User",
        },
    )

    user_id = create_response.json()["id"]

    response = client.patch(
        f"/users/{user_id}",
        json={
            "full_name": "Updated API User",
        },
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated API User"


def test_create_user_returns_409_when_email_already_exists(
    client: TestClient,
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Duplicate User API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle API 4",
            postal_code="41004",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    email = f"user-{uuid.uuid4().hex[:12]}@example.com"

    payload = {
        "business_id": business.id,
        "email": email,
        "password": "password123",
        "full_name": "Duplicate API User",
    }

    first_response = client.post(
        "/users",
        json=payload,
    )

    second_response = client.post(
        "/users",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_create_user_returns_404_when_business_does_not_exist(
    client: TestClient,
):
    response = client.post(
        "/users",
        json={
            "business_id": 999999,
            "email": f"user-{uuid.uuid4().hex[:12]}@example.com",
            "password": "password123",
            "full_name": "No Business User",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Business not found"


def test_deactivate_user(
    client: TestClient,
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Deactivate User API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle API 5",
            postal_code="41005",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    create_response = client.post(
        "/users",
        json={
            "business_id": business.id,
            "email": f"user-{uuid.uuid4().hex[:12]}@example.com",
            "password": "password123",
            "full_name": "Deactivate API User",
        },
    )

    user_id = create_response.json()["id"]

    response = client.patch(
        f"/users/{user_id}/deactivate"
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_activate_user(
    client: TestClient,
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Activate User API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle API 6",
            postal_code="41006",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    create_response = client.post(
        "/users",
        json={
            "business_id": business.id,
            "email": f"user-{uuid.uuid4().hex[:12]}@example.com",
            "password": "password123",
            "full_name": "Activate API User",
        },
    )

    user_id = create_response.json()["id"]

    client.patch(
        f"/users/{user_id}/deactivate"
    )

    response = client.patch(
        f"/users/{user_id}/activate"
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True