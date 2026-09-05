import uuid

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
            legal_name="User API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle API 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )


def create_user(
    db_session: Session,
    business_id: int,
    *,
    email: str | None = None,
    full_name: str = "API User",
):
    service = UserService(db_session)

    return service.create_user(
        UserCreate(
            business_id=business_id,
            email=(
                email
                or f"user-{uuid.uuid4().hex[:12]}@example.com"
            ),
            password="password123",
            full_name=full_name,
        )
    )


def get_auth_headers_for_business(
    client: TestClient,
    db_session: Session,
    business_id: int,
):
    email = f"auth-{uuid.uuid4().hex[:12]}@example.com"
    password = "password123"

    create_user(
        db_session,
        business_id,
        email=email,
        full_name="Authenticated User",
    )

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_user_in_authenticated_business(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    email = f"user-{uuid.uuid4().hex[:12]}@example.com"

    response = client.post(
        "/users",
        headers=headers,
        json={
            "email": email,
            "password": "password123",
            "full_name": "Created API User",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["business_id"] == business.id
    assert data["email"] == email
    assert data["full_name"] == "Created API User"
    assert data["is_active"] is True

    assert "password" not in data
    assert "password_hash" not in data


def test_create_user_does_not_accept_business_id(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(db_session)
    other_business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    response = client.post(
        "/users",
        headers=headers,
        json={
            "business_id": other_business.id,
            "email": f"user-{uuid.uuid4().hex[:12]}@example.com",
            "password": "password123",
            "full_name": "Cross Tenant User",
        },
    )

    assert response.status_code == 422


def test_create_user_without_authentication_returns_401(
    client: TestClient,
):
    response = client.post(
        "/users",
        json={
            "email": f"user-{uuid.uuid4().hex[:12]}@example.com",
            "password": "password123",
            "full_name": "Unauthenticated User",
        },
    )

    assert response.status_code == 401


def test_list_users_returns_only_authenticated_business(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(db_session)
    other_business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    own_user = create_user(
        db_session,
        own_business.id,
        full_name="Own Tenant User",
    )

    other_user = create_user(
        db_session,
        other_business.id,
        full_name="Other Tenant User",
    )

    response = client.get(
        "/users",
        headers=headers,
    )

    assert response.status_code == 200

    returned_ids = {
        user["id"]
        for user in response.json()
    }

    assert own_user.id in returned_ids
    assert other_user.id not in returned_ids

    assert all(
        user["business_id"] == own_business.id
        for user in response.json()
    )


def test_list_users_without_authentication_returns_401(
    client: TestClient,
):
    response = client.get("/users")

    assert response.status_code == 401


def test_get_own_business_user(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    user = create_user(
        db_session,
        business.id,
    )

    response = client.get(
        f"/users/{user.id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == user.id
    assert response.json()["business_id"] == business.id


def test_get_other_business_user_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(db_session)
    other_business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    other_user = create_user(
        db_session,
        other_business.id,
    )

    response = client.get(
        f"/users/{other_user.id}",
        headers=headers,
    )

    assert response.status_code == 404


def test_get_user_without_authentication_returns_401(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    user = create_user(
        db_session,
        business.id,
    )

    response = client.get(
        f"/users/{user.id}"
    )

    assert response.status_code == 401


def test_get_nonexistent_user_returns_404(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    response = client.get(
        "/users/999999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_update_own_business_user(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    user = create_user(
        db_session,
        business.id,
        full_name="Original API User",
    )

    response = client.patch(
        f"/users/{user.id}",
        headers=headers,
        json={
            "full_name": "Updated API User",
        },
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated API User"


def test_update_other_business_user_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(db_session)
    other_business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    other_user = create_user(
        db_session,
        other_business.id,
    )

    response = client.patch(
        f"/users/{other_user.id}",
        headers=headers,
        json={
            "full_name": "Forbidden Update",
        },
    )

    assert response.status_code == 404


def test_update_user_without_authentication_returns_401(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    user = create_user(
        db_session,
        business.id,
    )

    response = client.patch(
        f"/users/{user.id}",
        json={
            "full_name": "Unauthenticated Update",
        },
    )

    assert response.status_code == 401


def test_update_user_with_duplicate_email_returns_409(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    first_user = create_user(
        db_session,
        business.id,
    )

    second_user = create_user(
        db_session,
        business.id,
    )

    response = client.patch(
        f"/users/{second_user.id}",
        headers=headers,
        json={
            "email": first_user.email,
        },
    )

    assert response.status_code == 409


def test_deactivate_user_endpoint_is_not_exposed(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    user = create_user(
        db_session,
        business.id,
    )

    response = client.patch(
        f"/users/{user.id}/deactivate",
        headers=headers,
    )

    assert response.status_code == 404


def test_activate_user_endpoint_is_not_exposed(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    user = create_user(
        db_session,
        business.id,
    )

    response = client.patch(
        f"/users/{user.id}/activate",
        headers=headers,
    )

    assert response.status_code == 404