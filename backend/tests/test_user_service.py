import uuid

import pytest
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.user.schemas import UserCreate, UserUpdate
from app.domain.user.service import (
    InactiveUserError,
    InvalidUserCredentialsError,
    UserAlreadyExistsError,
    UserBusinessInactiveError,
    UserBusinessNotFoundError,
    UserService,
)


def test_create_user(db_session: Session):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="User Service Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Servicio 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = service.create_user(
        UserCreate(
            business_id=business.id,
            email=f"user-{uuid.uuid4().hex[:12]}@example.com",
            password="password123",
            full_name="Service User",
        )
    )

    assert user.id is not None
    assert user.business_id == business.id
    assert user.full_name == "Service User"
    assert user.is_active is True

    assert user.password_hash != "password123"
    assert verify_password(
        "password123",
        user.password_hash,
    )


def test_create_user_fails_when_business_does_not_exist(
    db_session: Session,
):
    service = UserService(db_session)

    data = UserCreate(
        business_id=999999,
        email=f"user-{uuid.uuid4().hex[:12]}@example.com",
        password="password123",
        full_name="Orphan User",
    )

    with pytest.raises(UserBusinessNotFoundError):
        service.create_user(data)


def test_create_user_fails_when_business_is_inactive(
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Inactive Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Inactiva 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    business.is_active = False
    db_session.flush()

    data = UserCreate(
        business_id=business.id,
        email=f"user-{uuid.uuid4().hex[:12]}@example.com",
        password="password123",
        full_name="Inactive Business User",
    )

    with pytest.raises(UserBusinessInactiveError):
        service.create_user(data)


def test_create_user_fails_when_email_already_exists(
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Duplicate Email Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Duplicada 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    email = f"user-{uuid.uuid4().hex[:12]}@example.com"

    service.create_user(
        UserCreate(
            business_id=business.id,
            email=email,
            password="password123",
            full_name="First User",
        )
    )

    duplicate_user = UserCreate(
        business_id=business.id,
        email=email,
        password="another-password",
        full_name="Duplicate User",
    )

    with pytest.raises(UserAlreadyExistsError):
        service.create_user(duplicate_user)


def test_get_user_by_id(db_session: Session):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Get User Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Get 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    created_user = service.create_user(
        UserCreate(
            business_id=business.id,
            email=f"user-{uuid.uuid4().hex[:12]}@example.com",
            password="password123",
            full_name="Get User",
        )
    )

    user = service.get_by_id(created_user.id)

    assert user is not None
    assert user.id == created_user.id


def test_update_user(db_session: Session):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Update Service Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Update 2",
            postal_code="41002",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = service.create_user(
        UserCreate(
            business_id=business.id,
            email=f"user-{uuid.uuid4().hex[:12]}@example.com",
            password="password123",
            full_name="Original User",
        )
    )

    updated_user = service.update_user(
        user.id,
        UserUpdate(full_name="Updated User"),
    )

    assert updated_user is not None
    assert updated_user.id == user.id
    assert updated_user.full_name == "Updated User"


def test_update_user_fails_when_email_already_exists(
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Duplicate Update Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Duplicate 2",
            postal_code="41003",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    first_email = f"user-{uuid.uuid4().hex[:12]}@example.com"
    second_email = f"user-{uuid.uuid4().hex[:12]}@example.com"

    first_user = service.create_user(
        UserCreate(
            business_id=business.id,
            email=first_email,
            password="password123",
            full_name="First User",
        )
    )

    service.create_user(
        UserCreate(
            business_id=business.id,
            email=second_email,
            password="password123",
            full_name="Second User",
        )
    )

    with pytest.raises(UserAlreadyExistsError):
        service.update_user(
            first_user.id,
            UserUpdate(email=second_email),
        )


def test_deactivate_user(db_session: Session):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Deactivate User Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Deactivate 1",
            postal_code="41004",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = service.create_user(
        UserCreate(
            business_id=business.id,
            email=f"user-{uuid.uuid4().hex[:12]}@example.com",
            password="password123",
            full_name="Active User",
        )
    )

    deactivated_user = service.deactivate_user(user.id)

    assert deactivated_user is not None
    assert deactivated_user.is_active is False


def test_activate_user(db_session: Session):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Activate User Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Activate 1",
            postal_code="41005",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = service.create_user(
        UserCreate(
            business_id=business.id,
            email=f"user-{uuid.uuid4().hex[:12]}@example.com",
            password="password123",
            full_name="Inactive User",
        )
    )

    service.deactivate_user(user.id)

    activated_user = service.activate_user(user.id)

    assert activated_user is not None
    assert activated_user.is_active is True


def test_deactivate_user_returns_none_when_user_does_not_exist(
    db_session: Session,
):
    service = UserService(db_session)

    assert service.deactivate_user(999999) is None


def test_activate_user_returns_none_when_user_does_not_exist(
    db_session: Session,
):
    service = UserService(db_session)

    assert service.activate_user(999999) is None


def test_authenticate_user_success(db_session: Session):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Auth Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Auth 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    created_user = service.create_user(
        UserCreate(
            business_id=business.id,
            email=f"auth-{uuid.uuid4().hex[:12]}@example.com",
            password="password123",
            full_name="Auth User",
        )
    )

    authenticated_user = service.authenticate_user(
        created_user.email,
        "password123",
    )

    assert authenticated_user.id == created_user.id


def test_authenticate_user_rejects_wrong_password(
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Wrong Password SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Password 1",
            postal_code="41002",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = service.create_user(
        UserCreate(
            business_id=business.id,
            email=f"wrong-{uuid.uuid4().hex[:12]}@example.com",
            password="password123",
            full_name="Wrong Password User",
        )
    )

    with pytest.raises(InvalidUserCredentialsError):
        service.authenticate_user(
            user.email,
            "incorrect-password",
        )


def test_authenticate_user_rejects_unknown_email(
    db_session: Session,
):
    service = UserService(db_session)

    with pytest.raises(InvalidUserCredentialsError):
        service.authenticate_user(
            "missing@example.com",
            "password123",
        )


def test_authenticate_user_rejects_inactive_user(
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Inactive User Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Inactive User 1",
            postal_code="41003",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = service.create_user(
        UserCreate(
            business_id=business.id,
            email=f"inactive-{uuid.uuid4().hex[:12]}@example.com",
            password="password123",
            full_name="Inactive User",
        )
    )

    service.deactivate_user(user.id)

    with pytest.raises(InactiveUserError):
        service.authenticate_user(
            user.email,
            "password123",
        )


def test_authenticate_user_rejects_inactive_business(
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Inactive Business Auth SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Inactive Business 1",
            postal_code="41004",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = service.create_user(
        UserCreate(
            business_id=business.id,
            email=(
                f"business-inactive-"
                f"{uuid.uuid4().hex[:12]}@example.com"
            ),
            password="password123",
            full_name="Inactive Business User",
        )
    )

    business.is_active = False
    db_session.flush()

    with pytest.raises(UserBusinessInactiveError):
        service.authenticate_user(
            user.email,
            "password123",
        )