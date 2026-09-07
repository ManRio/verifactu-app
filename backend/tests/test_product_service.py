import uuid
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.product.schemas import ProductCreate, ProductUpdate
from app.domain.product.service import (
    ProductAlreadyExistsError,
    ProductBusinessInactiveError,
    ProductBusinessNotFoundError,
    ProductService,
)


def create_business(
    db_session: Session,
):
    repository = BusinessRepository(db_session)

    return repository.create(
        BusinessCreate(
            legal_name="Product Service Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Producto 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )


def build_product_data(
    business_id: int,
    *,
    name: str = "Service Product",
    sku: str | None = None,
) -> ProductCreate:
    return ProductCreate(
        business_id=business_id,
        name=name,
        sku=(
            sku
            if sku is not None
            else f"SKU-{uuid.uuid4().hex[:12]}"
        ),
        description="Service product description",
        unit_price=Decimal("19.90"),
        tax_rate=Decimal("21.00"),
    )


def test_create_product(
    db_session: Session,
):
    business = create_business(db_session)
    service = ProductService(db_session)

    product = service.create_product(
        build_product_data(
            business.id,
            name="Mechanical Keyboard",
            sku="KEYBOARD-SERVICE-001",
        )
    )

    assert product.id is not None
    assert product.business_id == business.id
    assert product.name == "Mechanical Keyboard"
    assert product.sku == "KEYBOARD-SERVICE-001"
    assert product.unit_price == Decimal("19.90")
    assert product.tax_rate == Decimal("21.00")
    assert product.is_active is True


def test_create_product_fails_when_business_does_not_exist(
    db_session: Session,
):
    service = ProductService(db_session)

    data = build_product_data(
        999999999,
    )

    with pytest.raises(
        ProductBusinessNotFoundError
    ):
        service.create_product(data)


def test_create_product_fails_when_business_is_inactive(
    db_session: Session,
):
    business = create_business(db_session)
    service = ProductService(db_session)

    business.is_active = False
    db_session.flush()

    data = build_product_data(
        business.id,
    )

    with pytest.raises(
        ProductBusinessInactiveError
    ):
        service.create_product(data)


def test_create_product_rejects_duplicate_sku_in_same_business(
    db_session: Session,
):
    business = create_business(db_session)
    service = ProductService(db_session)

    service.create_product(
        build_product_data(
            business.id,
            sku="DUPLICATE-SERVICE-001",
        )
    )

    duplicate_product = build_product_data(
        business.id,
        sku="DUPLICATE-SERVICE-001",
    )

    with pytest.raises(
        ProductAlreadyExistsError
    ):
        service.create_product(
            duplicate_product
        )


def test_create_product_allows_same_sku_in_different_businesses(
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    service = ProductService(db_session)

    first_product = service.create_product(
        build_product_data(
            first_business.id,
            sku="SHARED-SERVICE-001",
        )
    )

    second_product = service.create_product(
        build_product_data(
            second_business.id,
            sku="SHARED-SERVICE-001",
        )
    )

    assert first_product.id != second_product.id

    assert first_product.business_id == (
        first_business.id
    )

    assert second_product.business_id == (
        second_business.id
    )

    assert first_product.sku == second_product.sku


def test_get_product_by_id(
    db_session: Session,
):
    business = create_business(db_session)
    service = ProductService(db_session)

    created_product = service.create_product(
        build_product_data(
            business.id,
        )
    )

    product = service.get_by_id(
        created_product.id
    )

    assert product is not None
    assert product.id == created_product.id
    assert product.business_id == business.id


def test_list_products_by_business_id(
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    service = ProductService(db_session)

    first_product = service.create_product(
        build_product_data(
            first_business.id,
            name="First Product",
        )
    )

    second_product = service.create_product(
        build_product_data(
            first_business.id,
            name="Second Product",
        )
    )

    other_product = service.create_product(
        build_product_data(
            second_business.id,
            name="Other Business Product",
        )
    )

    products = service.list_by_business_id(
        first_business.id
    )

    product_ids = [
        product.id
        for product in products
    ]

    assert product_ids == [
        first_product.id,
        second_product.id,
    ]

    assert other_product.id not in product_ids


def test_update_product(
    db_session: Session,
):
    business = create_business(db_session)
    service = ProductService(db_session)

    product = service.create_product(
        build_product_data(
            business.id,
            name="Original Product",
            sku="UPDATE-SERVICE-001",
        )
    )

    updated_product = service.update_product(
        product.id,
        ProductUpdate(
            name="Updated Product",
            unit_price=Decimal("29.95"),
        ),
    )

    assert updated_product is not None
    assert updated_product.id == product.id
    assert updated_product.name == "Updated Product"
    assert updated_product.unit_price == Decimal("29.95")

    assert updated_product.sku == (
        "UPDATE-SERVICE-001"
    )

    assert updated_product.business_id == (
        business.id
    )


def test_update_nonexistent_product_returns_none(
    db_session: Session,
):
    service = ProductService(db_session)

    updated_product = service.update_product(
        999999999,
        ProductUpdate(
            name="Missing Product",
        ),
    )

    assert updated_product is None


def test_update_product_rejects_duplicate_sku(
    db_session: Session,
):
    business = create_business(db_session)
    service = ProductService(db_session)

    first_product = service.create_product(
        build_product_data(
            business.id,
            sku="FIRST-SERVICE-001",
        )
    )

    second_product = service.create_product(
        build_product_data(
            business.id,
            sku="SECOND-SERVICE-001",
        )
    )

    with pytest.raises(
        ProductAlreadyExistsError
    ):
        service.update_product(
            second_product.id,
            ProductUpdate(
                sku=first_product.sku,
            ),
        )


def test_update_product_can_remove_sku(
    db_session: Session,
):
    business = create_business(db_session)
    service = ProductService(db_session)

    product = service.create_product(
        build_product_data(
            business.id,
            sku="REMOVE-SERVICE-001",
        )
    )

    updated_product = service.update_product(
        product.id,
        ProductUpdate(
            sku=None,
        ),
    )

    assert updated_product is not None
    assert updated_product.sku is None


def test_deactivate_product(
    db_session: Session,
):
    business = create_business(db_session)
    service = ProductService(db_session)

    product = service.create_product(
        build_product_data(
            business.id,
        )
    )

    deactivated_product = (
        service.deactivate_product(
            product.id,
        )
    )

    assert deactivated_product is not None
    assert deactivated_product.id == product.id
    assert deactivated_product.is_active is False


def test_deactivate_nonexistent_product_returns_none(
    db_session: Session,
):
    service = ProductService(db_session)

    deactivated_product = (
        service.deactivate_product(
            999999999,
        )
    )

    assert deactivated_product is None


def test_activate_product(
    db_session: Session,
):
    business = create_business(db_session)
    service = ProductService(db_session)

    product = service.create_product(
        build_product_data(
            business.id,
        )
    )

    service.deactivate_product(
        product.id
    )

    activated_product = service.activate_product(
        product.id
    )

    assert activated_product is not None
    assert activated_product.id == product.id
    assert activated_product.is_active is True


def test_activate_nonexistent_product_returns_none(
    db_session: Session,
):
    service = ProductService(db_session)

    activated_product = service.activate_product(
        999999999,
    )

    assert activated_product is None


def test_create_product_without_commit(
    db_session: Session,
):
    business = create_business(db_session)
    service = ProductService(db_session)

    sku = f"TRANSACTION-{uuid.uuid4().hex[:12]}"

    product = service.create_product(
        build_product_data(
            business.id,
            sku=sku,
        ),
        commit=False,
    )

    assert product.id is not None

    db_session.rollback()

    persisted_product = (
        service.repository.get_by_business_id_and_sku(
            business_id=business.id,
            sku=sku,
        )
    )

    assert persisted_product is None