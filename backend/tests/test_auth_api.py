import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import BusinessService
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def build_registration_payload(
    *,
    tax_id: str | None = None,
    email: str | None = None,
) -> dict:
    return {
        "business": {
            "legal_name": "Registered API Business SL",
            "tax_id": (
                tax_id
                or f"TEST-{uuid.uuid4().hex[:12]}"
            ),
            "address": "Calle Registro API 1",
            "postal_code": "41001",
            "city": "Sevilla",
            "province": "Sevilla",
            "country_code": "ES",
        },
        "user": {
            "email": (
                email
                or (
                    f"register-api-{uuid.uuid4().hex[:12]}"
                    "@example.com"
                )
            ),
            "password": "password123",
            "full_name": "Registered API User",
        },
    }


def test_register_creates_business_user_and_returns_access_token(
    client: TestClient,
    db_session: Session,
):
    payload = build_registration_payload()

    response = client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["token_type"] == "bearer"
    assert data["access_token"]

    business_repository = BusinessRepository(
        db_session
    )
    user_service = UserService(db_session)

    business = business_repository.get_by_tax_id(
        payload["business"]["tax_id"]
    )

    assert business is not None

    user = user_service.get_by_email(
        payload["user"]["email"]
    )

    assert user is not None
    assert user.business_id == business.id

    token_payload = decode_access_token(
        data["access_token"]
    )

    assert token_payload["sub"] == str(user.id)


def test_register_returns_token_usable_with_me(
    client: TestClient,
):
    payload = build_registration_payload()

    register_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert register_response.status_code == 201

    access_token = register_response.json()[
        "access_token"
    ]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == payload["user"]["email"]
    assert data["full_name"] == (
        payload["user"]["full_name"]
    )
    assert data["is_active"] is True


def test_register_normalizes_user_email(
    client: TestClient,
    db_session: Session,
):
    email = (
        f"Register-{uuid.uuid4().hex[:12]}"
        "@EXAMPLE.COM"
    )

    payload = build_registration_payload(
        email=email,
    )

    response = client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 201

    user_service = UserService(db_session)

    user = user_service.get_by_email(
        email,
    )

    assert user is not None
    assert user.email == email.lower()


def test_register_rejects_duplicate_tax_id(
    client: TestClient,
):
    tax_id = f"TEST-{uuid.uuid4().hex[:12]}"

    first_payload = build_registration_payload(
        tax_id=tax_id,
    )

    first_response = client.post(
        "/auth/register",
        json=first_payload,
    )

    assert first_response.status_code == 201

    second_payload = build_registration_payload(
        tax_id=tax_id,
    )

    response = client.post(
        "/auth/register",
        json=second_payload,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "A business with that tax ID already exists"
        )
    }


def test_register_rejects_duplicate_email_and_rolls_back_business(
    client: TestClient,
    db_session: Session,
):
    email = (
        f"duplicate-{uuid.uuid4().hex[:12]}"
        "@example.com"
    )

    first_payload = build_registration_payload(
        email=email,
    )

    first_response = client.post(
        "/auth/register",
        json=first_payload,
    )

    assert first_response.status_code == 201

    second_tax_id = (
        f"TEST-{uuid.uuid4().hex[:12]}"
    )

    second_payload = build_registration_payload(
        tax_id=second_tax_id,
        email=email.upper(),
    )

    response = client.post(
        "/auth/register",
        json=second_payload,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "A user with that email already exists"
        )
    }

    business_repository = BusinessRepository(
        db_session
    )

    rolled_back_business = (
        business_repository.get_by_tax_id(
            second_tax_id
        )
    )

    assert rolled_back_business is None


def test_login_returns_access_token(
    client: TestClient,
    db_session: Session,
):
    business_repository = BusinessRepository(
        db_session
    )
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
            email=(
                f"api-login-{uuid.uuid4().hex[:12]}"
                "@example.com"
            ),
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
    business_repository = BusinessRepository(
        db_session
    )
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
            email=(
                f"me-{uuid.uuid4().hex[:12]}"
                "@example.com"
            ),
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

    access_token = login_response.json()[
        "access_token"
    ]

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
    business_repository = BusinessRepository(
        db_session
    )
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

    access_token = login_response.json()[
        "access_token"
    ]

    user_service.deactivate_user(
        user.id
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


def test_get_me_rejects_token_after_business_deactivation(
    client: TestClient,
    db_session: Session,
):
    business_repository = BusinessRepository(
        db_session
    )
    business_service = BusinessService(
        db_session
    )
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

    access_token = login_response.json()[
        "access_token"
    ]

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