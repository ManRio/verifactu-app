import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.customer.schemas import CustomerCreate
from app.domain.customer.service import CustomerService
from app.domain.delivery_note.model import (
    DeliveryNote,
    DeliveryNoteLine,
)
from app.domain.delivery_note.repository import (
    DeliveryNoteRepository,
)
from app.domain.invoice.model import (
    Invoice,
    InvoiceDeliveryNote,
    InvoiceLine,
    InvoiceSeries,
)
from app.domain.invoice.repository import (
    InvoiceRepository,
    InvoiceSeriesRepository,
)
from app.domain.order.schemas import (
    OrderCreate,
    OrderLineInput,
)
from app.domain.order.service import OrderService
from app.domain.product.schemas import ProductCreate
from app.domain.product.service import ProductService


def create_business(
    db_session: Session,
):
    repository = BusinessRepository(
        db_session
    )

    return repository.create(
        BusinessCreate(
            legal_name="Invoice Repository Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Factura 1",
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
    service = CustomerService(
        db_session
    )

    return service.create_customer(
        CustomerCreate(
            business_id=business_id,
            tax_id=f"CUST-{uuid.uuid4().hex[:12]}",
            legal_name="Invoice Repository Customer",
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
    name: str = "Invoice Repository Product",
):
    service = ProductService(
        db_session
    )

    return service.create_product(
        ProductCreate(
            business_id=business_id,
            name=name,
            sku=f"INVOICE-{uuid.uuid4().hex[:12]}",
            description=(
                "Product used in invoice repository tests"
            ),
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
    service = OrderService(
        db_session
    )

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


def create_confirmed_delivery_note(
    db_session: Session,
    business_id: int,
    order_id: int,
    order_line_id: int,
    *,
    quantity: Decimal = Decimal("4.000"),
):
    repository = DeliveryNoteRepository(
        db_session
    )

    return repository.create(
        DeliveryNote(
            business_id=business_id,
            order_id=order_id,
            status="CONFIRMED",
            delivery_date=date(2026, 10, 1),
            notes="Invoice repository delivery note",
        ),
        [
            DeliveryNoteLine(
                order_line_id=order_line_id,
                description="Invoice Repository Product",
                quantity=quantity,
                unit_price=Decimal("10.00"),
                tax_rate=Decimal("21.00"),
                position=1,
            )
        ],
    )


def build_invoice(
    business,
    customer,
) -> Invoice:
    return Invoice(
        business_id=business.id,
        customer_id=customer.id,
        status="DRAFT",
        invoice_type="STANDARD",
        series=None,
        number=None,
        full_number=None,
        issue_date=None,
        operation_date=date(2026, 10, 1),
        issuer_legal_name=business.legal_name,
        issuer_tax_id=business.tax_id,
        issuer_address=business.address,
        issuer_postal_code=business.postal_code,
        issuer_city=business.city,
        issuer_province=business.province,
        issuer_country_code=business.country_code,
        customer_legal_name=customer.legal_name,
        customer_tax_id=customer.tax_id,
        customer_address=customer.address,
        customer_postal_code=customer.postal_code,
        customer_city=customer.city,
        customer_province=customer.province,
        customer_country_code=customer.country_code,
        subtotal=Decimal("40.00"),
        tax_total=Decimal("8.40"),
        total_amount=Decimal("48.40"),
        notes="Invoice repository test",
    )


def build_invoice_line(
    delivery_note_line: DeliveryNoteLine,
    *,
    position: int = 1,
) -> InvoiceLine:
    return InvoiceLine(
        delivery_note_line_id=delivery_note_line.id,
        order_line_id=delivery_note_line.order_line_id,
        description=delivery_note_line.description,
        quantity=delivery_note_line.quantity,
        unit_price=delivery_note_line.unit_price,
        tax_rate=delivery_note_line.tax_rate,
        base_amount=Decimal("40.00"),
        tax_amount=Decimal("8.40"),
        total_amount=Decimal("48.40"),
        position=position,
    )


def build_invoice_delivery_note(
    delivery_note_id: int,
) -> InvoiceDeliveryNote:
    return InvoiceDeliveryNote(
        delivery_note_id=delivery_note_id,
    )


def create_invoice_dependencies(
    db_session: Session,
):
    business = create_business(
        db_session
    )

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

    delivery_note = (
        create_confirmed_delivery_note(
            db_session,
            business.id,
            order.id,
            order.lines[0].id,
        )
    )

    return (
        business,
        customer,
        order,
        delivery_note,
    )


def test_create_invoice(
    db_session: Session,
):
    (
        business,
        customer,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    repository = InvoiceRepository(
        db_session
    )

    invoice = repository.create(
        build_invoice(
            business,
            customer,
        ),
        [
            build_invoice_line(
                delivery_note.lines[0]
            )
        ],
        [
            build_invoice_delivery_note(
                delivery_note.id
            )
        ],
    )

    assert invoice.id is not None
    assert invoice.business_id == business.id
    assert invoice.customer_id == customer.id
    assert invoice.status == "DRAFT"

    assert invoice.subtotal == Decimal(
        "40.00"
    )
    assert invoice.tax_total == Decimal(
        "8.40"
    )
    assert invoice.total_amount == Decimal(
        "48.40"
    )

    assert len(invoice.lines) == 1
    assert invoice.lines[0].id is not None

    assert (
        invoice.lines[0].delivery_note_line_id
        == delivery_note.lines[0].id
    )

    assert len(
        invoice.delivery_notes
    ) == 1

    assert (
        invoice.delivery_notes[0].delivery_note_id
        == delivery_note.id
    )


def test_get_invoice_by_id_includes_content(
    db_session: Session,
):
    (
        business,
        customer,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    repository = InvoiceRepository(
        db_session
    )

    created = repository.create(
        build_invoice(
            business,
            customer,
        ),
        [
            build_invoice_line(
                delivery_note.lines[0]
            )
        ],
        [
            build_invoice_delivery_note(
                delivery_note.id
            )
        ],
    )

    found = repository.get_by_id(
        created.id
    )

    assert found is not None
    assert found.id == created.id

    assert len(found.lines) == 1

    assert len(
        found.delivery_notes
    ) == 1


def test_get_nonexistent_invoice_returns_none(
    db_session: Session,
):
    repository = InvoiceRepository(
        db_session
    )

    assert (
        repository.get_by_id(
            999999999
        )
        is None
    )


def test_list_invoices_by_business_id(
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

    first_delivery_note = (
        create_confirmed_delivery_note(
            db_session,
            first_business.id,
            first_order.id,
            first_order.lines[0].id,
        )
    )

    second_delivery_note = (
        create_confirmed_delivery_note(
            db_session,
            second_business.id,
            second_order.id,
            second_order.lines[0].id,
        )
    )

    repository = InvoiceRepository(
        db_session
    )

    first_invoice = repository.create(
        build_invoice(
            first_business,
            first_customer,
        ),
        [
            build_invoice_line(
                first_delivery_note.lines[0]
            )
        ],
        [
            build_invoice_delivery_note(
                first_delivery_note.id
            )
        ],
    )

    other_invoice = repository.create(
        build_invoice(
            second_business,
            second_customer,
        ),
        [
            build_invoice_line(
                second_delivery_note.lines[0]
            )
        ],
        [
            build_invoice_delivery_note(
                second_delivery_note.id
            )
        ],
    )

    invoices = (
        repository.list_by_business_id(
            first_business.id
        )
    )

    invoice_ids = [
        invoice.id
        for invoice in invoices
    ]

    assert invoice_ids == [
        first_invoice.id
    ]

    assert (
        other_invoice.id
        not in invoice_ids
    )


def test_get_invoice_id_for_delivery_note(
    db_session: Session,
):
    (
        business,
        customer,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    repository = InvoiceRepository(
        db_session
    )

    invoice = repository.create(
        build_invoice(
            business,
            customer,
        ),
        [
            build_invoice_line(
                delivery_note.lines[0]
            )
        ],
        [
            build_invoice_delivery_note(
                delivery_note.id
            )
        ],
    )

    invoice_id = (
        repository
        .get_invoice_id_for_delivery_note(
            delivery_note.id
        )
    )

    assert invoice_id == invoice.id


def test_get_invoice_id_for_uninvoiced_delivery_note_returns_none(
    db_session: Session,
):
    (
        _,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    repository = InvoiceRepository(
        db_session
    )

    invoice_id = (
        repository
        .get_invoice_id_for_delivery_note(
            delivery_note.id
        )
    )

    assert invoice_id is None


def test_get_invoiced_delivery_note_ids(
    db_session: Session,
):
    business = create_business(
        db_session
    )

    customer = create_customer(
        db_session,
        business.id,
    )

    first_product = create_product(
        db_session,
        business.id,
        name="First Invoice Product",
    )

    second_product = create_product(
        db_session,
        business.id,
        name="Second Invoice Product",
    )

    first_order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        first_product.id,
    )

    second_order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        second_product.id,
    )

    first_delivery_note = (
        create_confirmed_delivery_note(
            db_session,
            business.id,
            first_order.id,
            first_order.lines[0].id,
        )
    )

    second_delivery_note = (
        create_confirmed_delivery_note(
            db_session,
            business.id,
            second_order.id,
            second_order.lines[0].id,
        )
    )

    repository = InvoiceRepository(
        db_session
    )

    repository.create(
        build_invoice(
            business,
            customer,
        ),
        [
            build_invoice_line(
                first_delivery_note.lines[0]
            )
        ],
        [
            build_invoice_delivery_note(
                first_delivery_note.id
            )
        ],
    )

    result = (
        repository
        .get_invoiced_delivery_note_ids(
            [
                first_delivery_note.id,
                second_delivery_note.id,
            ]
        )
    )

    assert result == {
        first_delivery_note.id
    }


def test_get_invoiced_delivery_note_ids_with_empty_list(
    db_session: Session,
):
    repository = InvoiceRepository(
        db_session
    )

    assert (
        repository
        .get_invoiced_delivery_note_ids(
            []
        )
        == set()
    )


def test_replace_invoice_content(
    db_session: Session,
):
    business = create_business(
        db_session
    )

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

    first_order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        first_product.id,
    )

    second_order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        second_product.id,
    )

    first_delivery_note = (
        create_confirmed_delivery_note(
            db_session,
            business.id,
            first_order.id,
            first_order.lines[0].id,
        )
    )

    second_delivery_note = (
        create_confirmed_delivery_note(
            db_session,
            business.id,
            second_order.id,
            second_order.lines[0].id,
        )
    )

    repository = InvoiceRepository(
        db_session
    )

    invoice = repository.create(
        build_invoice(
            business,
            customer,
        ),
        [
            build_invoice_line(
                first_delivery_note.lines[0]
            )
        ],
        [
            build_invoice_delivery_note(
                first_delivery_note.id
            )
        ],
    )

    original_line_id = (
        invoice.lines[0].id
    )

    original_link_id = (
        invoice.delivery_notes[0].id
    )

    updated = repository.replace_content(
        invoice,
        [
            build_invoice_line(
                second_delivery_note.lines[0]
            )
        ],
        [
            build_invoice_delivery_note(
                second_delivery_note.id
            )
        ],
    )

    assert len(updated.lines) == 1

    assert (
        updated.lines[0].delivery_note_line_id
        == second_delivery_note.lines[0].id
    )

    assert len(
        updated.delivery_notes
    ) == 1

    assert (
        updated.delivery_notes[0].delivery_note_id
        == second_delivery_note.id
    )

    orphaned_line = db_session.scalar(
        select(InvoiceLine).where(
            InvoiceLine.id
            == original_line_id
        )
    )

    orphaned_link = db_session.scalar(
        select(
            InvoiceDeliveryNote
        ).where(
            InvoiceDeliveryNote.id
            == original_link_id
        )
    )

    assert orphaned_line is None
    assert orphaned_link is None


def test_create_and_get_invoice_series(
    db_session: Session,
):
    business = create_business(
        db_session
    )

    repository = (
        InvoiceSeriesRepository(
            db_session
        )
    )

    created = repository.create(
        InvoiceSeries(
            business_id=business.id,
            code="F",
            next_number=1,
        )
    )

    found = (
        repository
        .get_by_business_and_code(
            business.id,
            "F",
        )
    )

    assert created.id is not None
    assert found is not None
    assert found.id == created.id
    assert found.code == "F"
    assert found.next_number == 1


def test_get_invoice_series_for_update(
    db_session: Session,
):
    business = create_business(
        db_session
    )

    repository = (
        InvoiceSeriesRepository(
            db_session
        )
    )

    created = repository.create(
        InvoiceSeries(
            business_id=business.id,
            code="F",
            next_number=1,
        )
    )

    found = (
        repository
        .get_by_business_and_code_for_update(
            business.id,
            "F",
        )
    )

    assert found is not None
    assert found.id == created.id
    assert found.code == "F"


def test_flush_invoice_series_changes(
    db_session: Session,
):
    business = create_business(
        db_session
    )

    repository = (
        InvoiceSeriesRepository(
            db_session
        )
    )

    invoice_series = repository.create(
        InvoiceSeries(
            business_id=business.id,
            code="F",
            next_number=1,
        )
    )

    invoice_series.next_number = 2

    updated = repository.flush(
        invoice_series
    )

    assert updated.next_number == 2

    found = (
        repository
        .get_by_business_and_code(
            business.id,
            "F",
        )
    )

    assert found is not None
    assert found.next_number == 2