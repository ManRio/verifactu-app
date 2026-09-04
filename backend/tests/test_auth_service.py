import uuid

import pytest
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.domain.auth.schemas import (
    LoginRequest,
    RegistrationRequest,
    RegistrationUserCreate,
)
from app.domain.auth.service import AuthService
from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserAlreadyExistsError, UserService


def test_login_returns_access_token(
    db_session: Session,
):
    business_repository = BusinessRepository(
        db_session
    )
    user_service = UserService(db_session)
    auth_service = AuthService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Auth Service Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Login 1",
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
                f"login-{uuid.uuid4().hex[:12]}"
                "@example.com"
            ),
            password="password123",
            full_name="Login User",
        )
    )

    response = auth_service.login(
        LoginRequest(
            email=user.email,
            password="password123",
        )
    )

    assert response.token_type == "bearer"
    assert response.access_token

    payload = decode_access_token(
        response.access_token,
    )

    assert payload["sub"] == str(user.id)


def test_register_creates_business_user_and_access_token(
    db_session: Session,
):
    auth_service = AuthService(db_session)
    user_service = UserService(db_session)
    business_repository = BusinessRepository(
        db_session
    )

    tax_id = f"TEST-{uuid.uuid4().hex[:12]}"
    email = (
        f"register-{uuid.uuid4().hex[:12]}"
        "@example.com"
    )

    response = auth_service.register(
        RegistrationRequest(
            business=BusinessCreate(
                legal_name="Registered Business SL",
                tax_id=tax_id,
                address="Calle Registro 1",
                postal_code="41001",
                city="Sevilla",
                province="Sevilla",
                country_code="ES",
            ),
            user=RegistrationUserCreate(
                email=email,
                password="password123",
                full_name="Registered User",
            ),
        )
    )

    assert response.token_type == "bearer"
    assert response.access_token

    business = business_repository.get_by_tax_id(
        tax_id
    )

    assert business is not None

    user = user_service.get_by_email(
        email
    )

    assert user is not None
    assert user.business_id == business.id

    payload = decode_access_token(
        response.access_token,
    )

    assert payload["sub"] == str(user.id)

def test_register_rolls_back_business_if_user_creation_fails(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    auth_service = AuthService(db_session)
    business_repository = BusinessRepository(
        db_session
    )

    tax_id = f"TEST-{uuid.uuid4().hex[:12]}"

    def fail_create_user(*args, **kwargs):
        raise UserAlreadyExistsError

    monkeypatch.setattr(
        auth_service.user_service,
        "create_user",
        fail_create_user,
    )

    with pytest.raises(UserAlreadyExistsError):
        auth_service.register(
            RegistrationRequest(
                business=BusinessCreate(
                    legal_name="Rollback Business SL",
                    tax_id=tax_id,
                    address="Calle Rollback 1",
                    postal_code="41001",
                    city="Sevilla",
                    province="Sevilla",
                    country_code="ES",
                ),
                user=RegistrationUserCreate(
                    email=(
                        f"rollback-{uuid.uuid4().hex[:12]}"
                        "@example.com"
                    ),
                    password="password123",
                    full_name="Rollback User",
                ),
            )
        )

    persisted_business = (
        business_repository.get_by_tax_id(
            tax_id
        )
    )

    assert persisted_business is None