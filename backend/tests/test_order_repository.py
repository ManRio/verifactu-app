import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.customer.schemas import CustomerCreate
from app.domain.customer.service import CustomerService
from app.domain.order.model import Order, OrderLine
from app.domain.order.repository import OrderRepository
from app.domain.product.schemas import ProductCreate
from app.domain.product.service import ProductService


def create_business(
    db_session: Session,
):
    repository = BusinessRepository(db_session)

    return repository.create(
        BusinessCreate(
            legal_name="Order Repository Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Pedido 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )


def create_customer(
    db_session: Session,
    business_id: int,
):
    service = CustomerService(db_session)

    return service.create_customer(
        CustomerCreate(
            business_id=business_id,
            tax_id=f"CUST-{uuid.uuid4().hex[:12]}",
            legal_name="Order Repository Customer",
            trade_name=None,
            address="Calle Cliente 10",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
            email="customer@example.com",
            phone="600123456",
        )
    )


def create_product(
    db_session: Session,
    business_id: int,
    *,
    name: str = "Order Repository Product",
):
    service = ProductService(db_session)

    return service.create_product(
        ProductCreate(
            business_id=business_id,
            name=name,
            sku=f"ORDER-{uuid.uuid4().hex[:12]}",
            description="Product used in order repository tests",
            unit_price=Decimal("10.00"),
            tax_rate=Decimal("21.00"),
        )
    )


def build_order(
    business_id: int,
    customer_id: int,
) -> Order:
    return Order(
        business_id=business_id,
        customer_id=customer_id,
        status="DRAFT",
        notes="Order repository test",
        subtotal=Decimal("20.00"),
        tax_total=Decimal("4.20"),
        total_amount=Decimal("24.20"),
    )


def build_order_line(
    product_id: int,
    *,
    description: str = "Repository Product",
    position: int = 1,
) -> OrderLine:
    return OrderLine(
        product_id=product_id,
        description=description,
        quantity=Decimal("2.000"),
        unit_price=Decimal("10.00"),
        tax_rate=Decimal("21.00"),
        base_amount=Decimal("20.00"),
        tax_amount=Decimal("4.20"),
        total_amount=Decimal("24.20"),
        position=position,
    )


def test_create_order(
    db_session: Session,
):
    business = create_business(db_session)
    customer = create_customer(
        db_session,
        business.id,
    )
    product = create_product(
        db_session,
        business.id,
    )

    repository = OrderRepository(db_session)

    order = repository.create(
        build_order(
            business.id,
            customer.id,
        ),
        [
            build_order_line(
                product.id,
            )
        ],
    )

    assert order.id is not None
    assert order.business_id == business.id
    assert order.customer_id == customer.id
    assert order.status == "DRAFT"
    assert order.subtotal == Decimal("20.00")
    assert order.tax_total == Decimal("4.20")
    assert order.total_amount == Decimal("24.20")

    assert len(order.lines) == 1
    assert order.lines[0].id is not None
    assert order.lines[0].order_id == order.id
    assert order.lines[0].product_id == product.id


def test_get_order_by_id_includes_lines(
    db_session: Session,
):
    business = create_business(db_session)
    customer = create_customer(
        db_session,
        business.id,
    )
    product = create_product(
        db_session,
        business.id,
    )

    repository = OrderRepository(db_session)

    created_order = repository.create(
        build_order(
            business.id,
            customer.id,
        ),
        [
            build_order_line(
                product.id,
            )
        ],
    )

    found_order = repository.get_by_id(
        created_order.id
    )

    assert found_order is not None
    assert found_order.id == created_order.id
    assert found_order.business_id == business.id
    assert found_order.customer_id == customer.id

    assert len(found_order.lines) == 1
    assert found_order.lines[0].product_id == product.id


def test_get_nonexistent_order_returns_none(
    db_session: Session,
):
    repository = OrderRepository(db_session)

    order = repository.get_by_id(
        999999999
    )

    assert order is None


def test_list_orders_by_business_id(
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    first_customer = create_customer(
        db_session,
        first_business.id,
    )

    second_customer = create_customer(
        db_session,
        second_business.id,
    )

    first_product = create_product(
        db_session,
        first_business.id,
    )

    second_product = create_product(
        db_session,
        second_business.id,
    )

    repository = OrderRepository(db_session)

    first_order = repository.create(
        build_order(
            first_business.id,
            first_customer.id,
        ),
        [
            build_order_line(
                first_product.id,
            )
        ],
    )

    second_order = repository.create(
        build_order(
            first_business.id,
            first_customer.id,
        ),
        [
            build_order_line(
                first_product.id,
            )
        ],
    )

    other_order = repository.create(
        build_order(
            second_business.id,
            second_customer.id,
        ),
        [
            build_order_line(
                second_product.id,
            )
        ],
    )

    orders = repository.list_by_business_id(
        first_business.id
    )

    order_ids = [
        order.id
        for order in orders
    ]

    assert order_ids == [
        first_order.id,
        second_order.id,
    ]

    assert other_order.id not in order_ids

    assert all(
        len(order.lines) == 1
        for order in orders
    )


def test_replace_order_lines(
    db_session: Session,
):
    business = create_business(db_session)
    customer = create_customer(
        db_session,
        business.id,
    )

    first_product = create_product(
        db_session,
        business.id,
        name="First Product",
    )

    second_product = create_product(
        db_session,
        business.id,
        name="Second Product",
    )

    repository = OrderRepository(db_session)

    order = repository.create(
        build_order(
            business.id,
            customer.id,
        ),
        [
            build_order_line(
                first_product.id,
                description="First Product",
            )
        ],
    )

    original_line_id = order.lines[0].id

    updated_order = repository.replace_lines(
        order,
        [
            build_order_line(
                second_product.id,
                description="Second Product",
            )
        ],
    )

    assert len(updated_order.lines) == 1
    assert updated_order.lines[0].id != original_line_id
    assert updated_order.lines[0].product_id == second_product.id
    assert updated_order.lines[0].description == "Second Product"


def test_replace_order_lines_deletes_orphaned_lines(
    db_session: Session,
):
    business = create_business(db_session)
    customer = create_customer(
        db_session,
        business.id,
    )

    first_product = create_product(
        db_session,
        business.id,
    )

    second_product = create_product(
        db_session,
        business.id,
    )

    repository = OrderRepository(db_session)

    order = repository.create(
        build_order(
            business.id,
            customer.id,
        ),
        [
            build_order_line(
                first_product.id,
            )
        ],
    )

    original_line_id = order.lines[0].id

    repository.replace_lines(
        order,
        [
            build_order_line(
                second_product.id,
            )
        ],
    )

    statement = select(OrderLine).where(
        OrderLine.id == original_line_id,
    )

    orphaned_line = db_session.scalar(
        statement
    )

    assert orphaned_line is None