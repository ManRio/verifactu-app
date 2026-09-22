import uuid

import pytest
from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.customer.schemas import CustomerCreate, CustomerUpdate
from app.domain.customer.service import (
    CustomerAlreadyExistsError,
    CustomerBusinessInactiveError,
    CustomerBusinessNotFoundError,
    CustomerService,
)


def create_business(
    db_session: Session,
):
    repository = BusinessRepository(db_session)

    return repository.create(
        BusinessCreate(
            legal_name="Customer Service Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Cliente 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )


def build_customer_data(
    business_id: int,
    *,
    legal_name: str = "Service Customer",
    tax_id: str | None = None,
) -> CustomerCreate:
    return CustomerCreate(
        business_id=business_id,
        tax_id=tax_id,
        legal_name=legal_name,
        trade_name="Customer Trade Name",
        address="Calle Cliente 10",
        postal_code="41001",
        city="Sevilla",
        province="Sevilla",
        country_code="ES",
        email="customer@example.com",
        phone="600123456",
    )


def test_create_customer(
    db_session: Session,
):
    business = create_business(db_session)
    service = CustomerService(db_session)

    customer = service.create_customer(
        build_customer_data(
            business.id,
            legal_name="Customer Example SL",
            tax_id="CUSTOMER-SERVICE-001",
        )
    )

    assert customer.id is not None
    assert customer.business_id == business.id
    assert customer.legal_name == "Customer Example SL"
    assert customer.tax_id == "CUSTOMER-SERVICE-001"
    assert customer.country_code == "ES"
    assert customer.is_active is True


def test_create_customer_fails_when_business_does_not_exist(
    db_session: Session,
):
    service = CustomerService(db_session)

    data = build_customer_data(
        999999999,
        tax_id="MISSING-BUSINESS-001",
    )

    with pytest.raises(
        CustomerBusinessNotFoundError
    ):
        service.create_customer(data)


def test_create_customer_fails_when_business_is_inactive(
    db_session: Session,
):
    business = create_business(db_session)
    service = CustomerService(db_session)

    business.is_active = False
    db_session.flush()

    data = build_customer_data(
        business.id,
        tax_id="INACTIVE-001",
    )

    with pytest.raises(
        CustomerBusinessInactiveError
    ):
        service.create_customer(data)


def test_create_customer_rejects_duplicate_tax_id_in_same_business(
    db_session: Session,
):
    business = create_business(db_session)
    service = CustomerService(db_session)

    service.create_customer(
        build_customer_data(
            business.id,
            tax_id="DUPLICATE-001",
        )
    )

    duplicate_customer = build_customer_data(
        business.id,
        tax_id="DUPLICATE-001",
    )

    with pytest.raises(
        CustomerAlreadyExistsError
    ):
        service.create_customer(
            duplicate_customer
        )


def test_create_customer_allows_same_tax_id_in_different_businesses(
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    service = CustomerService(db_session)

    first_customer = service.create_customer(
        build_customer_data(
            first_business.id,
            tax_id="SHARED-SERVICE-001",
        )
    )

    second_customer = service.create_customer(
        build_customer_data(
            second_business.id,
            tax_id="SHARED-SERVICE-001",
        )
    )

    assert first_customer.id != second_customer.id

    assert first_customer.business_id == (
        first_business.id
    )

    assert second_customer.business_id == (
        second_business.id
    )

    assert first_customer.tax_id == second_customer.tax_id


def test_create_customer_allows_multiple_customers_without_tax_id(
    db_session: Session,
):
    business = create_business(db_session)
    service = CustomerService(db_session)

    first_customer = service.create_customer(
        build_customer_data(
            business.id,
            legal_name="Customer Without Tax ID One",
        )
    )

    second_customer = service.create_customer(
        build_customer_data(
            business.id,
            legal_name="Customer Without Tax ID Two",
        )
    )

    assert first_customer.id != second_customer.id
    assert first_customer.tax_id is None
    assert second_customer.tax_id is None


def test_get_customer_by_id(
    db_session: Session,
):
    business = create_business(db_session)
    service = CustomerService(db_session)

    created_customer = service.create_customer(
        build_customer_data(
            business.id,
            tax_id="GET-SERVICE-001",
        )
    )

    customer = service.get_by_id(
        created_customer.id
    )

    assert customer is not None
    assert customer.id == created_customer.id
    assert customer.business_id == business.id


def test_list_customers_by_business_id(
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    service = CustomerService(db_session)

    first_customer = service.create_customer(
        build_customer_data(
            first_business.id,
            legal_name="First Customer",
            tax_id="LIST-SERVICE-001",
        )
    )

    second_customer = service.create_customer(
        build_customer_data(
            first_business.id,
            legal_name="Second Customer",
            tax_id="LIST-SERVICE-002",
        )
    )

    other_customer = service.create_customer(
        build_customer_data(
            second_business.id,
            legal_name="Other Business Customer",
            tax_id="LIST-SERVICE-003",
        )
    )

    customers = service.list_by_business_id(
        first_business.id
    )

    customer_ids = [
        customer.id
        for customer in customers
    ]

    assert customer_ids == [
        first_customer.id,
        second_customer.id,
    ]

    assert other_customer.id not in customer_ids


def test_update_customer(
    db_session: Session,
):
    business = create_business(db_session)
    service = CustomerService(db_session)

    customer = service.create_customer(
        build_customer_data(
            business.id,
            legal_name="Original Customer",
            tax_id="UPDATE-SERVICE-001",
        )
    )

    updated_customer = service.update_customer(
        customer.id,
        CustomerUpdate(
            legal_name="Updated Customer",
            city="Dos Hermanas",
            phone="611987654",
        ),
    )

    assert updated_customer is not None
    assert updated_customer.id == customer.id
    assert updated_customer.legal_name == "Updated Customer"
    assert updated_customer.city == "Dos Hermanas"
    assert updated_customer.phone == "611987654"

    assert updated_customer.tax_id == (
        "UPDATE-SERVICE-001"
    )

    assert updated_customer.business_id == (
        business.id
    )


def test_update_nonexistent_customer_returns_none(
    db_session: Session,
):
    service = CustomerService(db_session)

    updated_customer = service.update_customer(
        999999999,
        CustomerUpdate(
            legal_name="Missing Customer",
        ),
    )

    assert updated_customer is None


def test_update_customer_rejects_duplicate_tax_id(
    db_session: Session,
):
    business = create_business(db_session)
    service = CustomerService(db_session)

    first_customer = service.create_customer(
        build_customer_data(
            business.id,
            tax_id="FIRST-SERVICE-001",
        )
    )

    second_customer = service.create_customer(
        build_customer_data(
            business.id,
            tax_id="SECOND-SERVICE-001",
        )
    )

    with pytest.raises(
        CustomerAlreadyExistsError
    ):
        service.update_customer(
            second_customer.id,
            CustomerUpdate(
                tax_id=first_customer.tax_id,
            ),
        )


def test_update_customer_can_remove_tax_id(
    db_session: Session,
):
    business = create_business(db_session)
    service = CustomerService(db_session)

    customer = service.create_customer(
        build_customer_data(
            business.id,
            tax_id="REMOVE-SERVICE-001",
        )
    )

    updated_customer = service.update_customer(
        customer.id,
        CustomerUpdate(
            tax_id=None,
        ),
    )

    assert updated_customer is not None
    assert updated_customer.tax_id is None


def test_deactivate_customer(
    db_session: Session,
):
    business = create_business(db_session)
    service = CustomerService(db_session)

    customer = service.create_customer(
        build_customer_data(
            business.id,
            tax_id="DEACTIVATE-001",
        )
    )

    deactivated_customer = (
        service.deactivate_customer(
            customer.id,
        )
    )

    assert deactivated_customer is not None
    assert deactivated_customer.id == customer.id
    assert deactivated_customer.is_active is False


def test_deactivate_nonexistent_customer_returns_none(
    db_session: Session,
):
    service = CustomerService(db_session)

    deactivated_customer = (
        service.deactivate_customer(
            999999999,
        )
    )

    assert deactivated_customer is None


def test_activate_customer(
    db_session: Session,
):
    business = create_business(db_session)
    service = CustomerService(db_session)

    customer = service.create_customer(
        build_customer_data(
            business.id,
            tax_id="ACTIVATE-SERVICE-001",
        )
    )

    service.deactivate_customer(
        customer.id
    )

    activated_customer = service.activate_customer(
        customer.id
    )

    assert activated_customer is not None
    assert activated_customer.id == customer.id
    assert activated_customer.is_active is True


def test_activate_nonexistent_customer_returns_none(
    db_session: Session,
):
    service = CustomerService(db_session)

    activated_customer = service.activate_customer(
        999999999,
    )

    assert activated_customer is None


def test_create_customer_without_commit(
    db_session: Session,
):
    business = create_business(db_session)
    service = CustomerService(db_session)

    tax_id = f"TX-{uuid.uuid4().hex[:12]}"

    customer = service.create_customer(
        build_customer_data(
            business.id,
            tax_id=tax_id,
        ),
        commit=False,
    )

    assert customer.id is not None

    db_session.rollback()

    persisted_customer = (
        service.repository.get_by_business_id_and_tax_id(
            business_id=business.id,
            tax_id=tax_id,
        )
    )

    assert persisted_customer is None