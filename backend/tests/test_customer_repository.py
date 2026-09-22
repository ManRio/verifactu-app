import uuid

from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.customer.repository import CustomerRepository
from app.domain.customer.schemas import CustomerCreate, CustomerUpdate


def create_business(
    db_session: Session,
):
    repository = BusinessRepository(db_session)

    return repository.create(
        BusinessCreate(
            legal_name="Customer Repository Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Cliente 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )


def create_customer(
    repository: CustomerRepository,
    business_id: int,
    *,
    legal_name: str = "Repository Customer",
    tax_id: str | None = None,
):
    return repository.create(
        CustomerCreate(
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
    )


def test_create_customer(
    db_session: Session,
):
    business = create_business(db_session)
    repository = CustomerRepository(db_session)

    customer = repository.create(
        CustomerCreate(
            business_id=business.id,
            tax_id="CUSTOMER-001",
            legal_name="Customer Example SL",
            trade_name="Customer Example",
            address="Calle Ejemplo 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
            email="example@example.com",
            phone="600123456",
        )
    )

    assert customer.id is not None
    assert customer.business_id == business.id
    assert customer.tax_id == "CUSTOMER-001"
    assert customer.legal_name == "Customer Example SL"
    assert customer.trade_name == "Customer Example"
    assert customer.country_code == "ES"
    assert customer.is_active is True


def test_get_customer_by_id(
    db_session: Session,
):
    business = create_business(db_session)
    repository = CustomerRepository(db_session)

    created_customer = create_customer(
        repository,
        business.id,
        tax_id="LOOKUP-ID-001",
    )

    found_customer = repository.get_by_id(
        created_customer.id
    )

    assert found_customer is not None
    assert found_customer.id == created_customer.id
    assert found_customer.business_id == business.id
    assert found_customer.legal_name == created_customer.legal_name


def test_get_customer_by_business_id_and_tax_id(
    db_session: Session,
):
    business = create_business(db_session)
    repository = CustomerRepository(db_session)

    created_customer = create_customer(
        repository,
        business.id,
        tax_id="LOOKUP-TAX-001",
    )

    found_customer = (
        repository.get_by_business_id_and_tax_id(
            business_id=business.id,
            tax_id="LOOKUP-TAX-001",
        )
    )

    assert found_customer is not None
    assert found_customer.id == created_customer.id
    assert found_customer.tax_id == "LOOKUP-TAX-001"


def test_get_customer_by_tax_id_is_scoped_to_business(
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    repository = CustomerRepository(db_session)

    first_customer = create_customer(
        repository,
        first_business.id,
        tax_id="SHARED-TAX-001",
    )

    second_customer = create_customer(
        repository,
        second_business.id,
        tax_id="SHARED-TAX-001",
    )

    found_first = (
        repository.get_by_business_id_and_tax_id(
            business_id=first_business.id,
            tax_id="SHARED-TAX-001",
        )
    )

    found_second = (
        repository.get_by_business_id_and_tax_id(
            business_id=second_business.id,
            tax_id="SHARED-TAX-001",
        )
    )

    assert found_first is not None
    assert found_second is not None

    assert found_first.id == first_customer.id
    assert found_second.id == second_customer.id


def test_list_customers_by_business_id(
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    repository = CustomerRepository(db_session)

    first_customer = create_customer(
        repository,
        first_business.id,
        legal_name="First Customer",
        tax_id="LIST-001",
    )

    second_customer = create_customer(
        repository,
        first_business.id,
        legal_name="Second Customer",
        tax_id="LIST-002",
    )

    other_customer = create_customer(
        repository,
        second_business.id,
        legal_name="Other Business Customer",
        tax_id="LIST-003",
    )

    customers = repository.list_by_business_id(
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
    repository = CustomerRepository(db_session)

    customer = create_customer(
        repository,
        business.id,
        legal_name="Original Customer",
        tax_id="ORIGINAL-001",
    )

    updated_customer = repository.update(
        customer,
        CustomerUpdate(
            legal_name="Updated Customer",
            city="Dos Hermanas",
            phone="611987654",
        ),
    )

    assert updated_customer.id == customer.id
    assert updated_customer.legal_name == "Updated Customer"
    assert updated_customer.city == "Dos Hermanas"
    assert updated_customer.phone == "611987654"

    assert updated_customer.tax_id == "ORIGINAL-001"
    assert updated_customer.business_id == business.id
    assert updated_customer.country_code == "ES"


def test_update_customer_can_remove_tax_id(
    db_session: Session,
):
    business = create_business(db_session)
    repository = CustomerRepository(db_session)

    customer = create_customer(
        repository,
        business.id,
        tax_id="REMOVE-TAX-001",
    )

    updated_customer = repository.update(
        customer,
        CustomerUpdate(
            tax_id=None,
        ),
    )

    assert updated_customer.tax_id is None


def test_multiple_customers_can_have_no_tax_id(
    db_session: Session,
):
    business = create_business(db_session)
    repository = CustomerRepository(db_session)

    first_customer = create_customer(
        repository,
        business.id,
        legal_name="Customer Without Tax ID One",
    )

    second_customer = create_customer(
        repository,
        business.id,
        legal_name="Customer Without Tax ID Two",
    )

    assert first_customer.id is not None
    assert second_customer.id is not None
    assert first_customer.id != second_customer.id

    assert first_customer.tax_id is None
    assert second_customer.tax_id is None