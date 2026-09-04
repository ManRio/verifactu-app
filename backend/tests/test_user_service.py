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

def test_create_user_normalizes_email(
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Email Normalize SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Email 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = service.create_user(
        UserCreate(
            business_id=business.id,
            email="Normalize.User@Example.COM",
            password="password123",
            full_name="Normalize User",
        )
    )

    assert user.email == "normalize.user@example.com"


def test_authenticate_user_accepts_email_with_different_case(
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Email Auth Normalize SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Email 2",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    service.create_user(
        UserCreate(
            business_id=business.id,
            email="normalized@example.com",
            password="password123",
            full_name="Normalized User",
        )
    )

    user = service.authenticate_user(
        "NORMALIZED@EXAMPLE.COM",
        "password123",
    )

    assert user.email == "normalized@example.com"


def test_update_user_normalizes_email(
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Email Update Normalize SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Email 3",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = service.create_user(
        UserCreate(
            business_id=business.id,
            email="before@example.com",
            password="password123",
            full_name="Before User",
        )
    )

    updated_user = service.update_user(
        user.id,
        UserUpdate(
            email="After.User@Example.COM",
        ),
    )

    assert updated_user is not None
    assert updated_user.email == "after.user@example.com"

def test_create_user_rejects_duplicate_email_with_different_case(
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Case Duplicate Email SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Email 4",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    service.create_user(
        UserCreate(
            business_id=business.id,
            email="duplicate@example.com",
            password="password123",
            full_name="First User",
        )
    )

    duplicate_user = UserCreate(
        business_id=business.id,
        email="DUPLICATE@EXAMPLE.COM",
        password="password123",
        full_name="Duplicate User",
    )

    with pytest.raises(UserAlreadyExistsError):
        service.create_user(duplicate_user)

def test_get_by_email_accepts_different_case(
    db_session: Session,
):
    business_repository = BusinessRepository(db_session)
    service = UserService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Get By Email Normalize SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Email 5",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    created_user = service.create_user(
        UserCreate(
            business_id=business.id,
            email="lookup@example.com",
            password="password123",
            full_name="Lookup User",
        )
    )

    found_user = service.get_by_email(
        "LOOKUP@EXAMPLE.COM"
    )

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == "lookup@example.com"

def test_authenticate_nonexistent_user_runs_dummy_password_verification(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    service = UserService(db_session)

    dummy_verification_called = False

    def fake_verify_dummy_password(
        plain_password: str,
    ) -> None:
        nonlocal dummy_verification_called

        dummy_verification_called = True

        assert plain_password == "password123"

    monkeypatch.setattr(
        "app.domain.user.service.verify_dummy_password",
        fake_verify_dummy_password,
    )

    with pytest.raises(InvalidUserCredentialsError):
        service.authenticate_user(
            "nonexistent@example.com",
            "password123",
        )

    assert dummy_verification_called is True

def test_create_user_without_commit(
    db_session: Session,
):
    business_repository = BusinessRepository(
        db_session
    )

    business = business_repository.create(
        BusinessCreate(
            legal_name="Transactional User Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Usuario 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    service = UserService(db_session)

    email = (
        f"user-{uuid.uuid4().hex[:12]}"
        "@example.com"
    )

    user = service.create_user(
        UserCreate(
            business_id=business.id,
            email=email,
            password="password123",
            full_name="Transactional User",
        ),
        commit=False,
    )

    assert user.id is not None

    db_session.rollback()

    persisted_user = service.get_by_email(
        email
    )

    assert persisted_user is None