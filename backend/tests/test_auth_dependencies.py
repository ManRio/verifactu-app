import uuid

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.security import create_access_token
from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import BusinessService
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def create_test_user(
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    user_service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Auth Dependency Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Dependency 1",
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
                f"dependency-{uuid.uuid4().hex[:12]}"
                "@example.com"
            ),
            password="password123",
            full_name="Dependency User",
        )
    )

    return business, user


def bearer_credentials(
    token: str,
) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


def assert_credentials_exception(
    exc: HTTPException,
):
    assert exc.status_code == 401
    assert exc.detail == "Could not validate credentials"
    assert exc.headers == {
        "WWW-Authenticate": "Bearer",
    }


def test_get_current_user_returns_authenticated_user(
    db_session: Session,
):
    _, user = create_test_user(db_session)

    token = create_access_token(
        subject=str(user.id),
    )

    current_user = get_current_user(
        credentials=bearer_credentials(token),
        db=db_session,
    )

    assert current_user.id == user.id
    assert current_user.email == user.email


def test_get_current_user_rejects_missing_credentials(
    db_session: Session,
):
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=None,
            db=db_session,
        )

    assert_credentials_exception(exc_info.value)


def test_get_current_user_rejects_invalid_token(
    db_session: Session,
):
    credentials = bearer_credentials(
        "not-a-valid-token",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=credentials,
            db=db_session,
        )

    assert_credentials_exception(exc_info.value)


def test_get_current_user_rejects_invalid_subject(
    db_session: Session,
):
    token = create_access_token(
        subject="not-an-integer",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=bearer_credentials(token),
            db=db_session,
        )

    assert_credentials_exception(exc_info.value)


def test_get_current_user_rejects_nonexistent_user(
    db_session: Session,
):
    token = create_access_token(
        subject="999999999",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=bearer_credentials(token),
            db=db_session,
        )

    assert_credentials_exception(exc_info.value)


def test_get_current_user_rejects_inactive_user(
    db_session: Session,
):
    _, user = create_test_user(db_session)

    user_service = UserService(db_session)
    user_service.deactivate_user(user.id)

    token = create_access_token(
        subject=str(user.id),
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=bearer_credentials(token),
            db=db_session,
        )

    assert_credentials_exception(exc_info.value)


def test_get_current_user_rejects_inactive_business(
    db_session: Session,
):
    business, user = create_test_user(db_session)

    business_service = BusinessService(db_session)
    business_service.deactivate_business(
        business.id,
    )

    token = create_access_token(
        subject=str(user.id),
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=bearer_credentials(token),
            db=db_session,
        )

    assert_credentials_exception(exc_info.value)