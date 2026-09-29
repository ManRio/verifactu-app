import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.customer.schemas import CustomerCreate
from app.domain.customer.service import CustomerService
from app.domain.delivery_note.model import DeliveryNote, DeliveryNoteLine
from app.domain.delivery_note.repository import DeliveryNoteRepository
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
            legal_name="Delivery Repository Business SL",
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
            legal_name="Delivery Repository Customer",
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
    name: str = "Delivery Repository Product",
):
    service = ProductService(db_session)

    return service.create_product(
        ProductCreate(
            business_id=business_id,
            name=name,
            sku=f"DELIVERY-{uuid.uuid4().hex[:12]}",
            description="Product used in delivery repository tests",
            unit_price=Decimal("10.00"),
            tax_rate=Decimal("21.00"),
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
            lines=[
                OrderLineInput(
                    product_id=product_id,
                    quantity=quantity,
                    position=1,
                )
            ],
        )
    )

    confirmed = service.confirm_order(
        order.id
    )

    assert confirmed is not None

    return confirmed


def build_delivery_note(
    business_id: int,
    order_id: int,
    *,
    status: str = "DRAFT",
) -> DeliveryNote:
    return DeliveryNote(
        business_id=business_id,
        order_id=order_id,
        status=status,
        delivery_date=date(2026, 9, 29),
        notes="Delivery repository test",
    )


def build_delivery_note_line(
    order_line_id: int,
    *,
    quantity: Decimal = Decimal("4.000"),
    position: int = 1,
) -> DeliveryNoteLine:
    return DeliveryNoteLine(
        order_line_id=order_line_id,
        description="Delivery Repository Product",
        quantity=quantity,
        unit_price=Decimal("10.00"),
        tax_rate=Decimal("21.00"),
        position=position,
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

    repository = DeliveryNoteRepository(
        db_session
    )

    delivery_note = repository.create(
        build_delivery_note(
            business.id,
            order.id,
        ),
        [
            build_delivery_note_line(
                order.lines[0].id
            )
        ],
    )

    assert delivery_note.id is not None
    assert len(delivery_note.lines) == 1
    assert delivery_note.lines[0].id is not None


def test_get_delivery_note_by_id_includes_lines(
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

    repository = DeliveryNoteRepository(
        db_session
    )

    created = repository.create(
        build_delivery_note(
            business.id,
            order.id,
        ),
        [
            build_delivery_note_line(
                order.lines[0].id
            )
        ],
    )

    found = repository.get_by_id(
        created.id
    )

    assert found is not None
    assert found.id == created.id
    assert len(found.lines) == 1


def test_get_nonexistent_delivery_note_returns_none(
    db_session: Session,
):
    repository = DeliveryNoteRepository(
        db_session
    )

    assert (
        repository.get_by_id(
            999999999
        )
        is None
    )


def test_list_delivery_notes_by_business_id(
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

    repository = DeliveryNoteRepository(
        db_session
    )

    first_note = repository.create(
        build_delivery_note(
            first_business.id,
            first_order.id,
        ),
        [
            build_delivery_note_line(
                first_order.lines[0].id
            )
        ],
    )

    repository.create(
        build_delivery_note(
            second_business.id,
            second_order.id,
        ),
        [
            build_delivery_note_line(
                second_order.lines[0].id
            )
        ],
    )

    result = repository.list_by_business_id(
        first_business.id
    )

    assert [
        note.id
        for note in result
    ] == [
        first_note.id
    ]


def test_list_delivery_notes_by_order_id(
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

    repository = DeliveryNoteRepository(
        db_session
    )

    first_note = repository.create(
        build_delivery_note(
            business.id,
            first_order.id,
        ),
        [
            build_delivery_note_line(
                first_order.lines[0].id
            )
        ],
    )

    repository.create(
        build_delivery_note(
            business.id,
            second_order.id,
        ),
        [
            build_delivery_note_line(
                second_order.lines[0].id
            )
        ],
    )

    result = repository.list_by_order_id(
        first_order.id
    )

    assert [
        note.id
        for note in result
    ] == [
        first_note.id
    ]


def test_replace_delivery_note_lines(
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

    confirmed = order_service.confirm_order(
        order.id
    )

    assert confirmed is not None

    repository = DeliveryNoteRepository(
        db_session
    )

    delivery_note = repository.create(
        build_delivery_note(
            business.id,
            confirmed.id,
        ),
        [
            build_delivery_note_line(
                confirmed.lines[0].id,
                quantity=Decimal("2.000"),
            )
        ],
    )

    updated = repository.replace_lines(
        delivery_note,
        [
            DeliveryNoteLine(
                order_line_id=confirmed.lines[1].id,
                description="Second Product",
                quantity=Decimal("3.000"),
                unit_price=Decimal("10.00"),
                tax_rate=Decimal("21.00"),
                position=1,
            )
        ],
    )

    assert len(updated.lines) == 1
    assert (
        updated.lines[0].order_line_id
        == confirmed.lines[1].id
    )
    assert updated.lines[0].quantity == Decimal(
        "3.000"
    )


def test_replace_delivery_note_lines_deletes_orphaned_lines(
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

    repository = DeliveryNoteRepository(
        db_session
    )

    delivery_note = repository.create(
        build_delivery_note(
            business.id,
            order.id,
        ),
        [
            build_delivery_note_line(
                order.lines[0].id
            )
        ],
    )

    original_line_id = (
        delivery_note.lines[0].id
    )

    repository.replace_lines(
        delivery_note,
        [
            build_delivery_note_line(
                order.lines[0].id,
                quantity=Decimal("2.000"),
            )
        ],
    )

    statement = select(
        DeliveryNoteLine
    ).where(
        DeliveryNoteLine.id
        == original_line_id
    )

    assert db_session.scalar(
        statement
    ) is None


def test_confirmed_quantity_ignores_draft_delivery_notes(
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

    repository = DeliveryNoteRepository(
        db_session
    )

    repository.create(
        build_delivery_note(
            business.id,
            order.id,
            status="DRAFT",
        ),
        [
            build_delivery_note_line(
                order.lines[0].id,
                quantity=Decimal("4.000"),
            )
        ],
    )

    quantity = (
        repository
        .get_confirmed_quantity_for_order_line(
            order.lines[0].id
        )
    )

    assert quantity == Decimal(0)


def test_confirmed_quantity_sums_confirmed_delivery_notes(
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

    repository = DeliveryNoteRepository(
        db_session
    )

    repository.create(
        build_delivery_note(
            business.id,
            order.id,
            status="CONFIRMED",
        ),
        [
            build_delivery_note_line(
                order.lines[0].id,
                quantity=Decimal("4.000"),
            )
        ],
    )

    repository.create(
        build_delivery_note(
            business.id,
            order.id,
            status="CONFIRMED",
        ),
        [
            build_delivery_note_line(
                order.lines[0].id,
                quantity=Decimal("3.000"),
            )
        ],
    )

    quantity = (
        repository
        .get_confirmed_quantity_for_order_line(
            order.lines[0].id
        )
    )

    assert quantity == Decimal("7.000")


def test_confirmed_quantity_ignores_cancelled_delivery_notes(
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

    repository = DeliveryNoteRepository(
        db_session
    )

    repository.create(
        build_delivery_note(
            business.id,
            order.id,
            status="CONFIRMED",
        ),
        [
            build_delivery_note_line(
                order.lines[0].id,
                quantity=Decimal("4.000"),
            )
        ],
    )

    repository.create(
        build_delivery_note(
            business.id,
            order.id,
            status="CANCELLED",
        ),
        [
            build_delivery_note_line(
                order.lines[0].id,
                quantity=Decimal("5.000"),
            )
        ],
    )

    quantity = (
        repository
        .get_confirmed_quantity_for_order_line(
            order.lines[0].id
        )
    )

    assert quantity == Decimal("4.000")