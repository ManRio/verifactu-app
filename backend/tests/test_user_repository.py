import uuid

from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserUpdate


def test_create_user(db_session: Session):
    business_repository = BusinessRepository(db_session)
    user_repository = UserRepository(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="User Test Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Usuario 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = user_repository.create(
        business_id=business.id,
        email=f"user-{uuid.uuid4().hex[:12]}@example.com",
        password_hash="fake-hash-for-repository-test",
        full_name="Test User",
    )

    assert user.id is not None
    assert user.business_id == business.id
    assert user.password_hash == "fake-hash-for-repository-test"
    assert user.full_name == "Test User"
    assert user.is_active is True

def test_get_user_by_id(db_session: Session):
    business_repository = BusinessRepository(db_session)
    user_repository = UserRepository(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="User Lookup Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Usuario 2",
            postal_code="41002",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    created_user = user_repository.create(
        business_id=business.id,
        email=f"user-{uuid.uuid4().hex[:12]}@example.com",
        password_hash="fake-hash",
        full_name="Lookup User",
    )

    found_user = user_repository.get_by_id(created_user.id)

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == created_user.email


def test_get_user_by_email(db_session: Session):
    business_repository = BusinessRepository(db_session)
    user_repository = UserRepository(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="User Email Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Usuario 3",
            postal_code="41003",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    email = f"user-{uuid.uuid4().hex[:12]}@example.com"

    created_user = user_repository.create(
        business_id=business.id,
        email=email,
        password_hash="fake-hash",
        full_name="Email User",
    )

    found_user = user_repository.get_by_email(email)

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == email


def test_list_users_by_business_id(db_session: Session):
    business_repository = BusinessRepository(db_session)
    user_repository = UserRepository(db_session)

    first_business = business_repository.create(
        BusinessCreate(
            legal_name="First Users Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Empresa 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    second_business = business_repository.create(
        BusinessCreate(
            legal_name="Second Users Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Empresa 2",
            postal_code="41002",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    first_user = user_repository.create(
        business_id=first_business.id,
        email=f"user-{uuid.uuid4().hex[:12]}@example.com",
        password_hash="fake-hash",
        full_name="First User",
    )

    second_user = user_repository.create(
        business_id=first_business.id,
        email=f"user-{uuid.uuid4().hex[:12]}@example.com",
        password_hash="fake-hash",
        full_name="Second User",
    )

    user_repository.create(
        business_id=second_business.id,
        email=f"user-{uuid.uuid4().hex[:12]}@example.com",
        password_hash="fake-hash",
        full_name="Other Business User",
    )

    users = user_repository.list_by_business_id(first_business.id)

    assert [user.id for user in users] == [
        first_user.id,
        second_user.id,
    ]

def test_update_user(db_session: Session):
    business_repository = BusinessRepository(db_session)
    user_repository = UserRepository(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Update User Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Update 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = user_repository.create(
        business_id=business.id,
        email=f"user-{uuid.uuid4().hex[:12]}@example.com",
        password_hash="fake-hash",
        full_name="Original Name",
    )

    updated_user = user_repository.update(
        user,
        UserUpdate(
            full_name="Updated Name",
        ),
    )

    assert updated_user.id == user.id
    assert updated_user.full_name == "Updated Name"