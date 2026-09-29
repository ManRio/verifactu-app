import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.customer.schemas import CustomerCreate
from app.domain.customer.service import CustomerService
from app.domain.delivery_note.schemas import (
    DeliveryNoteCreate,
    DeliveryNoteLineInput,
    DeliveryNoteUpdate,
)
from app.domain.delivery_note.service import (
    DeliveryNoteBusinessInactiveError,
    DeliveryNoteBusinessNotFoundError,
    DeliveryNoteCannotCancelError,
    DeliveryNoteCannotConfirmError,
    DeliveryNoteDuplicateOrderLineError,
    DeliveryNoteDuplicatePositionError,
    DeliveryNoteNotEditableError,
    DeliveryNoteOrderLineNotFoundError,
    DeliveryNoteOrderNotConfirmedError,
    DeliveryNoteOrderNotFoundError,
    DeliveryNoteOrderTenantError,
    DeliveryNoteQuantityExceedsOrderedError,
    DeliveryNoteQuantityExceedsRemainingError,
    DeliveryNoteService,
)
from app.domain.order.schemas import OrderCreate, OrderLineInput
from app.domain.order.service import OrderService
from app.domain.product.schemas import ProductCreate
from app.domain.product.service import ProductService


def create_business(
    db_session: Session,
):
    repository = BusinessRepository(db_session)

    return repository.create(
        BusinessCreate(
            legal_name="Delivery Note Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Albaran 1",
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
            legal_name="Delivery Note Customer",
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
    name: str = "Delivery Note Product",
    unit_price: Decimal = Decimal("10.00"),
    tax_rate: Decimal = Decimal("21.00"),
):
    service = ProductService(db_session)

    return service.create_product(
        ProductCreate(
            business_id=business_id,
            name=name,
            sku=f"DELIVERY-{uuid.uuid4().hex[:12]}",
            description="Product used in delivery note tests",
            unit_price=unit_price,
            tax_rate=tax_rate,
        )
    )


def create_confirmed_order(
    db_session: Session,
    business_id: int,
    customer_id: int,
    product_id: int,
    *,
    quantity: Decimal = Decimal("10.000"),
):
    service = OrderService(db_session)

    order = service.create_order(
        OrderCreate(
            business_id=business_id,
            customer_id=customer_id,
            notes="Delivery note test order",
            lines=[
                OrderLineInput(
                    product_id=product_id,
                    quantity=quantity,
                    position=1,
                )
            ],
        )
    )

    confirmed_order = service.confirm_order(
        order.id
    )

    assert confirmed_order is not None

    return confirmed_order


def build_delivery_note_data(
    business_id: int,
    order_id: int,
    order_line_id: int,
    *,
    quantity: Decimal = Decimal("4.000"),
):
    return DeliveryNoteCreate(
        business_id=business_id,
        order_id=order_id,
        delivery_date=date(2026, 9, 29),
        notes="Delivery note test",
        lines=[
            DeliveryNoteLineInput(
                order_line_id=order_line_id,
                quantity=quantity,
                position=1,
            )
        ],
    )


def test_create_delivery_note(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    delivery_note = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
        )
    )

    assert delivery_note.id is not None
    assert delivery_note.business_id == business.id
    assert delivery_note.order_id == order.id
    assert delivery_note.status == "DRAFT"
    assert delivery_note.delivery_date == date(
        2026,
        9,
        29,
    )
    assert delivery_note.notes == "Delivery note test"
    assert len(delivery_note.lines) == 1


def test_create_delivery_note_snapshots_order_line(
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
        name="Snapshot Product",
        unit_price=Decimal("12.50"),
        tax_rate=Decimal("10.00"),
    )

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    delivery_note = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
        )
    )

    line = delivery_note.lines[0]

    assert line.description == "Snapshot Product"
    assert line.unit_price == Decimal("12.50")
    assert line.tax_rate == Decimal("10.00")
    assert line.quantity == Decimal("4.000")


def test_create_delivery_note_with_missing_business(
    db_session: Session,
):
    service = DeliveryNoteService(
        db_session
    )

    with pytest.raises(
        DeliveryNoteBusinessNotFoundError
    ):
        service.create_delivery_note(
            DeliveryNoteCreate(
                business_id=999999999,
                order_id=1,
                delivery_date=date(
                    2026,
                    9,
                    29,
                ),
                lines=[
                    DeliveryNoteLineInput(
                        order_line_id=1,
                        quantity=Decimal("1.000"),
                        position=1,
                    )
                ],
            )
        )


def test_create_delivery_note_with_inactive_business(
    db_session: Session,
):
    business = create_business(db_session)
    business.is_active = False
    db_session.flush()

    service = DeliveryNoteService(
        db_session
    )

    with pytest.raises(
        DeliveryNoteBusinessInactiveError
    ):
        service.create_delivery_note(
            DeliveryNoteCreate(
                business_id=business.id,
                order_id=1,
                delivery_date=date(
                    2026,
                    9,
                    29,
                ),
                lines=[
                    DeliveryNoteLineInput(
                        order_line_id=1,
                        quantity=Decimal("1.000"),
                        position=1,
                    )
                ],
            )
        )


def test_create_delivery_note_with_missing_order(
    db_session: Session,
):
    business = create_business(db_session)

    service = DeliveryNoteService(
        db_session
    )

    with pytest.raises(
        DeliveryNoteOrderNotFoundError
    ):
        service.create_delivery_note(
            DeliveryNoteCreate(
                business_id=business.id,
                order_id=999999999,
                delivery_date=date(
                    2026,
                    9,
                    29,
                ),
                lines=[
                    DeliveryNoteLineInput(
                        order_line_id=1,
                        quantity=Decimal("1.000"),
                        position=1,
                    )
                ],
            )
        )


def test_create_delivery_note_with_order_from_other_business(
    db_session: Session,
):
    own_business = create_business(
        db_session
    )
    other_business = create_business(
        db_session
    )

    customer = create_customer(
        db_session,
        other_business.id,
    )

    product = create_product(
        db_session,
        other_business.id,
    )

    order = create_confirmed_order(
        db_session,
        other_business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    with pytest.raises(
        DeliveryNoteOrderTenantError
    ):
        service.create_delivery_note(
            build_delivery_note_data(
                own_business.id,
                order.id,
                order.lines[0].id,
            )
        )


def test_create_delivery_note_requires_confirmed_order(
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

    order_service = OrderService(
        db_session
    )

    order = order_service.create_order(
        OrderCreate(
            business_id=business.id,
            customer_id=customer.id,
            lines=[
                OrderLineInput(
                    product_id=product.id,
                    quantity=Decimal("10.000"),
                    position=1,
                )
            ],
        )
    )

    service = DeliveryNoteService(
        db_session
    )

    with pytest.raises(
        DeliveryNoteOrderNotConfirmedError
    ):
        service.create_delivery_note(
            build_delivery_note_data(
                business.id,
                order.id,
                order.lines[0].id,
            )
        )


def test_create_delivery_note_rejects_order_line_from_other_order(
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

    first_order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    second_order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    with pytest.raises(
        DeliveryNoteOrderLineNotFoundError
    ):
        service.create_delivery_note(
            build_delivery_note_data(
                business.id,
                first_order.id,
                second_order.lines[0].id,
            )
        )


def test_create_delivery_note_rejects_quantity_above_ordered(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
        quantity=Decimal("10.000"),
    )

    service = DeliveryNoteService(
        db_session
    )

    with pytest.raises(
        DeliveryNoteQuantityExceedsOrderedError
    ):
        service.create_delivery_note(
            build_delivery_note_data(
                business.id,
                order.id,
                order.lines[0].id,
                quantity=Decimal("11.000"),
            )
        )


def test_create_delivery_note_rejects_duplicate_positions(
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

    order_service = OrderService(
        db_session
    )

    order = order_service.create_order(
        OrderCreate(
            business_id=business.id,
            customer_id=customer.id,
            lines=[
                OrderLineInput(
                    product_id=first_product.id,
                    quantity=Decimal("5.000"),
                    position=1,
                ),
                OrderLineInput(
                    product_id=second_product.id,
                    quantity=Decimal("5.000"),
                    position=2,
                ),
            ],
        )
    )

    confirmed_order = (
        order_service.confirm_order(
            order.id
        )
    )

    assert confirmed_order is not None

    service = DeliveryNoteService(
        db_session
    )

    with pytest.raises(
        DeliveryNoteDuplicatePositionError
    ):
        service.create_delivery_note(
            DeliveryNoteCreate(
                business_id=business.id,
                order_id=confirmed_order.id,
                delivery_date=date(
                    2026,
                    9,
                    29,
                ),
                lines=[
                    DeliveryNoteLineInput(
                        order_line_id=confirmed_order.lines[0].id,
                        quantity=Decimal("1.000"),
                        position=1,
                    ),
                    DeliveryNoteLineInput(
                        order_line_id=confirmed_order.lines[1].id,
                        quantity=Decimal("1.000"),
                        position=1,
                    ),
                ],
            )
        )


def test_create_delivery_note_rejects_duplicate_order_line(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    with pytest.raises(
        DeliveryNoteDuplicateOrderLineError
    ):
        service.create_delivery_note(
            DeliveryNoteCreate(
                business_id=business.id,
                order_id=order.id,
                delivery_date=date(
                    2026,
                    9,
                    29,
                ),
                lines=[
                    DeliveryNoteLineInput(
                        order_line_id=order.lines[0].id,
                        quantity=Decimal("2.000"),
                        position=1,
                    ),
                    DeliveryNoteLineInput(
                        order_line_id=order.lines[0].id,
                        quantity=Decimal("2.000"),
                        position=2,
                    ),
                ],
            )
        )


def test_get_delivery_note_by_id(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    created = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
        )
    )

    found = service.get_by_id(
        created.id
    )

    assert found is not None
    assert found.id == created.id
    assert len(found.lines) == 1


def test_list_delivery_notes_by_business(
    db_session: Session,
):
    first_business = create_business(
        db_session
    )
    second_business = create_business(
        db_session
    )

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

    first_order = create_confirmed_order(
        db_session,
        first_business.id,
        first_customer.id,
        first_product.id,
    )

    second_order = create_confirmed_order(
        db_session,
        second_business.id,
        second_customer.id,
        second_product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    first_note = service.create_delivery_note(
        build_delivery_note_data(
            first_business.id,
            first_order.id,
            first_order.lines[0].id,
        )
    )

    service.create_delivery_note(
        build_delivery_note_data(
            second_business.id,
            second_order.id,
            second_order.lines[0].id,
        )
    )

    delivery_notes = (
        service.list_by_business_id(
            first_business.id
        )
    )

    assert [
        note.id
        for note in delivery_notes
    ] == [
        first_note.id
    ]


def test_update_draft_delivery_note(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    delivery_note = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
        )
    )

    updated = service.update_delivery_note(
        delivery_note.id,
        DeliveryNoteUpdate(
            delivery_date=date(
                2026,
                9,
                30,
            ),
            notes="Updated delivery note",
            lines=[
                DeliveryNoteLineInput(
                    order_line_id=order.lines[0].id,
                    quantity=Decimal("3.000"),
                    position=1,
                )
            ],
        ),
    )

    assert updated is not None
    assert updated.delivery_date == date(
        2026,
        9,
        30,
    )
    assert updated.notes == "Updated delivery note"
    assert len(updated.lines) == 1
    assert updated.lines[0].quantity == Decimal(
        "3.000"
    )


def test_confirm_delivery_note(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    delivery_note = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
        )
    )

    confirmed = service.confirm_delivery_note(
        delivery_note.id
    )

    assert confirmed is not None
    assert confirmed.status == "CONFIRMED"
    assert confirmed.confirmed_at is not None


def test_partial_deliveries_can_complete_order(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
        quantity=Decimal("10.000"),
    )

    service = DeliveryNoteService(
        db_session
    )

    first = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
            quantity=Decimal("4.000"),
        )
    )

    service.confirm_delivery_note(
        first.id
    )

    second = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
            quantity=Decimal("6.000"),
        )
    )

    confirmed_second = (
        service.confirm_delivery_note(
            second.id
        )
    )

    assert confirmed_second is not None

    delivered_quantity = (
        service.repository
        .get_confirmed_quantity_for_order_line(
            order.lines[0].id
        )
    )

    assert delivered_quantity == Decimal(
        "10.000"
    )


def test_confirm_rejects_quantity_above_remaining(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
        quantity=Decimal("10.000"),
    )

    service = DeliveryNoteService(
        db_session
    )

    first = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
            quantity=Decimal("6.000"),
        )
    )

    service.confirm_delivery_note(
        first.id
    )

    second = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
            quantity=Decimal("5.000"),
        )
    )

    with pytest.raises(
        DeliveryNoteQuantityExceedsRemainingError
    ):
        service.confirm_delivery_note(
            second.id
        )


def test_cancel_confirmed_delivery_note_releases_quantity(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
        quantity=Decimal("10.000"),
    )

    service = DeliveryNoteService(
        db_session
    )

    first = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
            quantity=Decimal("6.000"),
        )
    )

    service.confirm_delivery_note(
        first.id
    )

    service.cancel_delivery_note(
        first.id
    )

    second = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
            quantity=Decimal("10.000"),
        )
    )

    confirmed_second = (
        service.confirm_delivery_note(
            second.id
        )
    )

    assert confirmed_second is not None
    assert confirmed_second.status == "CONFIRMED"


def test_confirmed_delivery_note_cannot_be_updated(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    delivery_note = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
        )
    )

    service.confirm_delivery_note(
        delivery_note.id
    )

    with pytest.raises(
        DeliveryNoteNotEditableError
    ):
        service.update_delivery_note(
            delivery_note.id,
            DeliveryNoteUpdate(
                notes="Forbidden edit",
            ),
        )


def test_delivery_note_cannot_be_confirmed_twice(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    delivery_note = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
        )
    )

    service.confirm_delivery_note(
        delivery_note.id
    )

    with pytest.raises(
        DeliveryNoteCannotConfirmError
    ):
        service.confirm_delivery_note(
            delivery_note.id
        )


def test_cancel_draft_delivery_note(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    delivery_note = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
        )
    )

    cancelled = service.cancel_delivery_note(
        delivery_note.id
    )

    assert cancelled is not None
    assert cancelled.status == "CANCELLED"


def test_cancel_confirmed_delivery_note(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    delivery_note = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
        )
    )

    service.confirm_delivery_note(
        delivery_note.id
    )

    cancelled = service.cancel_delivery_note(
        delivery_note.id
    )

    assert cancelled is not None
    assert cancelled.status == "CANCELLED"


def test_cancelled_delivery_note_cannot_be_cancelled_again(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    delivery_note = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
        )
    )

    service.cancel_delivery_note(
        delivery_note.id
    )

    with pytest.raises(
        DeliveryNoteCannotCancelError
    ):
        service.cancel_delivery_note(
            delivery_note.id
        )


def test_create_delivery_note_without_commit_can_be_rolled_back(
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

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    service = DeliveryNoteService(
        db_session
    )

    delivery_note = service.create_delivery_note(
        build_delivery_note_data(
            business.id,
            order.id,
            order.lines[0].id,
        ),
        commit=False,
    )

    delivery_note_id = delivery_note.id

    db_session.rollback()

    assert (
        service.get_by_id(
            delivery_note_id
        )
        is None
    )