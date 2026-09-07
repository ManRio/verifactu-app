import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.product.repository import ProductRepository
from app.domain.product.schemas import ProductCreate, ProductUpdate


def create_business(
    db_session: Session,
):
    repository = BusinessRepository(db_session)

    return repository.create(
        BusinessCreate(
            legal_name="Product Repository Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Producto 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )


def create_product(
    repository: ProductRepository,
    business_id: int,
    *,
    name: str = "Repository Product",
    sku: str | None = None,
):
    return repository.create(
        ProductCreate(
            business_id=business_id,
            name=name,
            sku=(
                sku
                if sku is not None
                else f"SKU-{uuid.uuid4().hex[:12]}"
            ),
            description="Repository product description",
            unit_price=Decimal("19.90"),
            tax_rate=Decimal("21.00"),
        )
    )


def test_create_product(
    db_session: Session,
):
    business = create_business(db_session)
    repository = ProductRepository(db_session)

    product = repository.create(
        ProductCreate(
            business_id=business.id,
            name="Mechanical Keyboard",
            sku="KEYBOARD-REPO-001",
            description="Mechanical keyboard",
            unit_price=Decimal("59.90"),
            tax_rate=Decimal("21.00"),
        )
    )

    assert product.id is not None
    assert product.business_id == business.id
    assert product.name == "Mechanical Keyboard"
    assert product.sku == "KEYBOARD-REPO-001"
    assert product.unit_price == Decimal("59.90")
    assert product.tax_rate == Decimal("21.00")
    assert product.is_active is True


def test_get_product_by_id(
    db_session: Session,
):
    business = create_business(db_session)
    repository = ProductRepository(db_session)

    created_product = create_product(
        repository,
        business.id,
    )

    found_product = repository.get_by_id(
        created_product.id
    )

    assert found_product is not None
    assert found_product.id == created_product.id
    assert found_product.business_id == business.id
    assert found_product.name == created_product.name


def test_get_product_by_business_id_and_sku(
    db_session: Session,
):
    business = create_business(db_session)
    repository = ProductRepository(db_session)

    created_product = create_product(
        repository,
        business.id,
        sku="LOOKUP-001",
    )

    found_product = (
        repository.get_by_business_id_and_sku(
            business_id=business.id,
            sku="LOOKUP-001",
        )
    )

    assert found_product is not None
    assert found_product.id == created_product.id
    assert found_product.sku == "LOOKUP-001"


def test_get_product_by_sku_is_scoped_to_business(
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    repository = ProductRepository(db_session)

    first_product = create_product(
        repository,
        first_business.id,
        sku="SHARED-REPO-001",
    )

    second_product = create_product(
        repository,
        second_business.id,
        sku="SHARED-REPO-001",
    )

    found_first = (
        repository.get_by_business_id_and_sku(
            business_id=first_business.id,
            sku="SHARED-REPO-001",
        )
    )

    found_second = (
        repository.get_by_business_id_and_sku(
            business_id=second_business.id,
            sku="SHARED-REPO-001",
        )
    )

    assert found_first is not None
    assert found_second is not None

    assert found_first.id == first_product.id
    assert found_second.id == second_product.id


def test_list_products_by_business_id(
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    repository = ProductRepository(db_session)

    first_product = create_product(
        repository,
        first_business.id,
        name="First Product",
    )

    second_product = create_product(
        repository,
        first_business.id,
        name="Second Product",
    )

    other_product = create_product(
        repository,
        second_business.id,
        name="Other Business Product",
    )

    products = repository.list_by_business_id(
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
    repository = ProductRepository(db_session)

    product = create_product(
        repository,
        business.id,
        name="Original Product",
        sku="ORIGINAL-001",
    )

    updated_product = repository.update(
        product,
        ProductUpdate(
            name="Updated Product",
            unit_price=Decimal("29.95"),
        ),
    )

    assert updated_product.id == product.id
    assert updated_product.name == "Updated Product"
    assert updated_product.unit_price == Decimal("29.95")

    assert updated_product.sku == "ORIGINAL-001"
    assert updated_product.business_id == business.id
    assert updated_product.tax_rate == Decimal("21.00")


def test_update_product_can_remove_sku(
    db_session: Session,
):
    business = create_business(db_session)
    repository = ProductRepository(db_session)

    product = create_product(
        repository,
        business.id,
        sku="REMOVE-REPO-001",
    )

    updated_product = repository.update(
        product,
        ProductUpdate(
            sku=None,
        ),
    )

    assert updated_product.sku is None