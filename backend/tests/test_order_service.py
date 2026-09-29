import uuid
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.customer.schemas import CustomerCreate
from app.domain.customer.service import CustomerService
from app.domain.order.schemas import OrderCreate, OrderLineInput, OrderUpdate
from app.domain.order.service import (
    OrderBusinessInactiveError,
    OrderBusinessNotFoundError,
    OrderCannotCancelError,
    OrderCannotConfirmError,
    OrderCustomerInactiveError,
    OrderCustomerNotFoundError,
    OrderCustomerTenantError,
    OrderDuplicatePositionError,
    OrderNotEditableError,
    OrderProductInactiveError,
    OrderProductNotFoundError,
    OrderProductTenantError,
    OrderService,
)
from app.domain.product.schemas import ProductCreate
from app.domain.product.service import ProductService


def create_business(
    db_session: Session,
):
    repository = BusinessRepository(db_session)

    return repository.create(
        BusinessCreate(
            legal_name="Order Service Business SL",
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
    *,
    legal_name: str = "Order Service Customer",
):
    service = CustomerService(db_session)

    return service.create_customer(
        CustomerCreate(
            business_id=business_id,
            tax_id=f"CUST-{uuid.uuid4().hex[:12]}",
            legal_name=legal_name,
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
    name: str = "Order Service Product",
    unit_price: Decimal = Decimal("10.00"),
    tax_rate: Decimal = Decimal("21.00"),
):
    service = ProductService(db_session)

    return service.create_product(
        ProductCreate(
            business_id=business_id,
            name=name,
            sku=f"ORDER-{uuid.uuid4().hex[:12]}",
            description="Product used in order tests",
            unit_price=unit_price,
            tax_rate=tax_rate,
        )
    )


def build_order_data(
    business_id: int,
    customer_id: int,
    product_id: int,
    *,
    quantity: Decimal = Decimal("2.000"),
) -> OrderCreate:
    return OrderCreate(
        business_id=business_id,
        customer_id=customer_id,
        notes="Order service test",
        lines=[
            OrderLineInput(
                product_id=product_id,
                quantity=quantity,
                position=1,
            )
        ],
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

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
        )
    )

    assert order.id is not None
    assert order.business_id == business.id
    assert order.customer_id == customer.id
    assert order.status == "DRAFT"
    assert order.notes == "Order service test"

    assert order.subtotal == Decimal("20.00")
    assert order.tax_total == Decimal("4.20")
    assert order.total_amount == Decimal("24.20")

    assert len(order.lines) == 1


def test_create_order_copies_product_snapshot(
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
        name="Caja de refrescos",
        unit_price=Decimal("18.50"),
        tax_rate=Decimal("21.00"),
    )

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
            quantity=Decimal("3.000"),
        )
    )

    line = order.lines[0]

    assert line.product_id == product.id
    assert line.description == "Caja de refrescos"
    assert line.quantity == Decimal("3.000")
    assert line.unit_price == Decimal("18.50")
    assert line.tax_rate == Decimal("21.00")


def test_create_order_calculates_line_amounts(
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
        unit_price=Decimal("10.50"),
        tax_rate=Decimal("21.00"),
    )

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
            quantity=Decimal("3.000"),
        )
    )

    line = order.lines[0]

    assert line.base_amount == Decimal("31.50")
    assert line.tax_amount == Decimal("6.62")
    assert line.total_amount == Decimal("38.12")

    assert order.subtotal == Decimal("31.50")
    assert order.tax_total == Decimal("6.62")
    assert order.total_amount == Decimal("38.12")


def test_create_order_rounds_money_half_up(
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
        unit_price=Decimal("0.05"),
        tax_rate=Decimal("10.00"),
    )

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
            quantity=Decimal("1.000"),
        )
    )

    line = order.lines[0]

    assert line.base_amount == Decimal("0.05")
    assert line.tax_amount == Decimal("0.01")
    assert line.total_amount == Decimal("0.06")


def test_create_order_calculates_multiple_lines(
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
        unit_price=Decimal("10.00"),
        tax_rate=Decimal("21.00"),
    )

    second_product = create_product(
        db_session,
        business.id,
        name="Second Product",
        unit_price=Decimal("5.00"),
        tax_rate=Decimal("10.00"),
    )

    service = OrderService(db_session)

    order = service.create_order(
        OrderCreate(
            business_id=business.id,
            customer_id=customer.id,
            notes=None,
            lines=[
                OrderLineInput(
                    product_id=first_product.id,
                    quantity=Decimal("2.000"),
                    position=1,
                ),
                OrderLineInput(
                    product_id=second_product.id,
                    quantity=Decimal("3.000"),
                    position=2,
                ),
            ],
        )
    )

    assert len(order.lines) == 2

    assert order.subtotal == Decimal("35.00")
    assert order.tax_total == Decimal("5.70")
    assert order.total_amount == Decimal("40.70")


def test_create_order_fails_when_business_does_not_exist(
    db_session: Session,
):
    service = OrderService(db_session)

    data = OrderCreate(
        business_id=999999999,
        customer_id=999999999,
        notes=None,
        lines=[
            OrderLineInput(
                product_id=999999999,
                quantity=Decimal("1.000"),
                position=1,
            )
        ],
    )

    with pytest.raises(
        OrderBusinessNotFoundError
    ):
        service.create_order(data)


def test_create_order_fails_when_business_is_inactive(
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

    business.is_active = False
    db_session.flush()

    service = OrderService(db_session)

    with pytest.raises(
        OrderBusinessInactiveError
    ):
        service.create_order(
            build_order_data(
                business.id,
                customer.id,
                product.id,
            )
        )


def test_create_order_fails_when_customer_does_not_exist(
    db_session: Session,
):
    business = create_business(db_session)
    product = create_product(
        db_session,
        business.id,
    )

    service = OrderService(db_session)

    with pytest.raises(
        OrderCustomerNotFoundError
    ):
        service.create_order(
            build_order_data(
                business.id,
                999999999,
                product.id,
            )
        )


def test_create_order_fails_when_customer_is_inactive(
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

    customer.is_active = False
    db_session.flush()

    service = OrderService(db_session)

    with pytest.raises(
        OrderCustomerInactiveError
    ):
        service.create_order(
            build_order_data(
                business.id,
                customer.id,
                product.id,
            )
        )


def test_create_order_rejects_customer_from_other_business(
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    customer = create_customer(
        db_session,
        second_business.id,
    )

    product = create_product(
        db_session,
        first_business.id,
    )

    service = OrderService(db_session)

    with pytest.raises(
        OrderCustomerTenantError
    ):
        service.create_order(
            build_order_data(
                first_business.id,
                customer.id,
                product.id,
            )
        )


def test_create_order_fails_when_product_does_not_exist(
    db_session: Session,
):
    business = create_business(db_session)

    customer = create_customer(
        db_session,
        business.id,
    )

    service = OrderService(db_session)

    with pytest.raises(
        OrderProductNotFoundError
    ):
        service.create_order(
            build_order_data(
                business.id,
                customer.id,
                999999999,
            )
        )


def test_create_order_fails_when_product_is_inactive(
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

    product.is_active = False
    db_session.flush()

    service = OrderService(db_session)

    with pytest.raises(
        OrderProductInactiveError
    ):
        service.create_order(
            build_order_data(
                business.id,
                customer.id,
                product.id,
            )
        )


def test_create_order_rejects_product_from_other_business(
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    customer = create_customer(
        db_session,
        first_business.id,
    )

    product = create_product(
        db_session,
        second_business.id,
    )

    service = OrderService(db_session)

    with pytest.raises(
        OrderProductTenantError
    ):
        service.create_order(
            build_order_data(
                first_business.id,
                customer.id,
                product.id,
            )
        )


def test_create_order_rejects_duplicate_positions(
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

    service = OrderService(db_session)

    data = OrderCreate(
        business_id=business.id,
        customer_id=customer.id,
        notes=None,
        lines=[
            OrderLineInput(
                product_id=first_product.id,
                quantity=Decimal("1.000"),
                position=1,
            ),
            OrderLineInput(
                product_id=second_product.id,
                quantity=Decimal("1.000"),
                position=1,
            ),
        ],
    )

    with pytest.raises(
        OrderDuplicatePositionError
    ):
        service.create_order(data)


def test_get_order_by_id(
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

    service = OrderService(db_session)

    created_order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
        )
    )

    order = service.get_by_id(
        created_order.id
    )

    assert order is not None
    assert order.id == created_order.id
    assert order.business_id == business.id
    assert len(order.lines) == 1


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

    service = OrderService(db_session)

    first_order = service.create_order(
        build_order_data(
            first_business.id,
            first_customer.id,
            first_product.id,
        )
    )

    second_order = service.create_order(
        build_order_data(
            first_business.id,
            first_customer.id,
            first_product.id,
        )
    )

    other_order = service.create_order(
        build_order_data(
            second_business.id,
            second_customer.id,
            second_product.id,
        )
    )

    orders = service.list_by_business_id(
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


def test_create_order_without_commit(
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

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
        ),
        commit=False,
    )

    assert order.id is not None

    order_id = order.id

    db_session.rollback()

    persisted_order = service.repository.get_by_id(
        order_id
    )

    assert persisted_order is None

def test_update_draft_order_notes(
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

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
        )
    )

    updated_order = service.update_order(
        order.id,
        OrderUpdate(
            notes="Updated order notes",
        ),
    )

    assert updated_order is not None
    assert updated_order.notes == "Updated order notes"
    assert updated_order.status == "DRAFT"


def test_update_draft_order_replaces_lines_and_recalculates_totals(
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
        unit_price=Decimal("10.00"),
        tax_rate=Decimal("21.00"),
    )

    second_product = create_product(
        db_session,
        business.id,
        name="Second Product",
        unit_price=Decimal("5.00"),
        tax_rate=Decimal("10.00"),
    )

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            first_product.id,
        )
    )

    updated_order = service.update_order(
        order.id,
        OrderUpdate(
            lines=[
                OrderLineInput(
                    product_id=second_product.id,
                    quantity=Decimal("3.000"),
                    position=1,
                )
            ],
        ),
    )

    assert updated_order is not None
    assert len(updated_order.lines) == 1

    line = updated_order.lines[0]

    assert line.product_id == second_product.id
    assert line.description == "Second Product"
    assert line.base_amount == Decimal("15.00")
    assert line.tax_amount == Decimal("1.50")
    assert line.total_amount == Decimal("16.50")

    assert updated_order.subtotal == Decimal("15.00")
    assert updated_order.tax_total == Decimal("1.50")
    assert updated_order.total_amount == Decimal("16.50")


def test_update_nonexistent_order_returns_none(
    db_session: Session,
):
    service = OrderService(db_session)

    updated_order = service.update_order(
        999999999,
        OrderUpdate(
            notes="Missing order",
        ),
    )

    assert updated_order is None


def test_confirm_order(
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

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
        )
    )

    confirmed_order = service.confirm_order(
        order.id
    )

    assert confirmed_order is not None
    assert confirmed_order.status == "CONFIRMED"
    assert confirmed_order.confirmed_at is not None


def test_confirmed_order_cannot_be_updated(
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

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
        )
    )

    service.confirm_order(
        order.id
    )

    with pytest.raises(
        OrderNotEditableError
    ):
        service.update_order(
            order.id,
            OrderUpdate(
                notes="This must not be allowed",
            ),
        )


def test_confirmed_order_cannot_be_confirmed_again(
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

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
        )
    )

    service.confirm_order(
        order.id
    )

    with pytest.raises(
        OrderCannotConfirmError
    ):
        service.confirm_order(
            order.id
        )


def test_cancel_draft_order(
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

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
        )
    )

    cancelled_order = service.cancel_order(
        order.id
    )

    assert cancelled_order is not None
    assert cancelled_order.status == "CANCELLED"


def test_cancel_confirmed_order(
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

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
        )
    )

    service.confirm_order(
        order.id
    )

    cancelled_order = service.cancel_order(
        order.id
    )

    assert cancelled_order is not None
    assert cancelled_order.status == "CANCELLED"


def test_cancelled_order_cannot_be_cancelled_again(
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

    service = OrderService(db_session)

    order = service.create_order(
        build_order_data(
            business.id,
            customer.id,
            product.id,
        )
    )

    service.cancel_order(
        order.id
    )

    with pytest.raises(
        OrderCannotCancelError
    ):
        service.cancel_order(
            order.id
        )