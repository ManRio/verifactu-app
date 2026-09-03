import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import BusinessService
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def test_login_returns_access_token(
    client: TestClient,
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    user_service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Auth API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Auth API 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = user_service.create_user(
        UserCreate(
            business_id=business.id,
            email=f"api-login-{uuid.uuid4().hex[:12]}@example.com",
            password="password123",
            full_name="Auth API User",
        )
    )

    response = client.post(
        "/auth/login",
        json={
            "email": user.email,
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert data["access_token"]

    payload = decode_access_token(
        data["access_token"],
    )

    assert payload["sub"] == str(user.id)

def test_login_rejects_invalid_credentials(
    client: TestClient,
):
    response = client.post(
        "/auth/login",
        json={
            "email": "does-not-exist@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Incorrect email or password"
    }
    assert response.headers["www-authenticate"] == "Bearer"

def test_get_me_returns_authenticated_user(
    client: TestClient,
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    user_service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Auth Me Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Me 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = user_service.create_user(
        UserCreate(
            business_id=business.id,
            email=f"me-{uuid.uuid4().hex[:12]}@example.com",
            password="password123",
            full_name="Authenticated User",
        )
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": user.email,
            "password": "password123",
        },
    )

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user.id
    assert data["email"] == user.email
    assert data["business_id"] == business.id
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data


def test_get_me_rejects_missing_token(
    client: TestClient,
):
    response = client.get(
        "/auth/me",
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials"
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_me_rejects_invalid_token(
    client: TestClient,
):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials"
    }
    assert response.headers["www-authenticate"] == "Bearer"

def test_get_me_rejects_token_after_user_deactivation(
    client: TestClient,
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    user_service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Inactive User Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Inactive User 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = user_service.create_user(
        UserCreate(
            business_id=business.id,
            email=(
                f"inactive-user-{uuid.uuid4().hex[:12]}"
                "@example.com"
            ),
            password="password123",
            full_name="Inactive User",
        )
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": user.email,
            "password": "password123",
        },
    )

    access_token = login_response.json()["access_token"]

    user_service.deactivate_user(user.id)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials"
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_me_rejects_token_after_business_deactivation(
    client: TestClient,
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    business_service = BusinessService(db_session)
    user_service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Inactive Business Auth SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Inactive Business 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = user_service.create_user(
        UserCreate(
            business_id=business.id,
            email=(
                f"inactive-business-{uuid.uuid4().hex[:12]}"
                "@example.com"
            ),
            password="password123",
            full_name="Business Inactive User",
        )
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": user.email,
            "password": "password123",
        },
    )

    access_token = login_response.json()["access_token"]

    business_service.deactivate_business(
        business.id,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials"
    }
    assert response.headers["www-authenticate"] == "Bearer"