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
)
from app.domain.delivery_note.service import DeliveryNoteService
from app.domain.invoice.schemas import (
    InvoiceCreate,
    InvoiceIssue,
    InvoiceUpdate,
)
from app.domain.invoice.service import (
    InvoiceBusinessInactiveError,
    InvoiceBusinessNotFoundError,
    InvoiceCannotIssueError,
    InvoiceDeliveryNoteAlreadyInvoicedError,
    InvoiceDeliveryNoteNotConfirmedError,
    InvoiceDeliveryNoteNotFoundError,
    InvoiceDeliveryNoteTenantError,
    InvoiceDuplicateDeliveryNoteError,
    InvoiceMixedCustomerError,
    InvoiceNotEditableError,
    InvoiceService,
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
            legal_name="Invoice Service Business SL",
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
    *,
    legal_name: str = "Invoice Service Customer",
):
    service = CustomerService(
        db_session
    )

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
    name: str = "Invoice Service Product",
    unit_price: Decimal = Decimal("10.00"),
    tax_rate: Decimal = Decimal("21.00"),
):
    service = ProductService(
        db_session
    )

    return service.create_product(
        ProductCreate(
            business_id=business_id,
            name=name,
            sku=f"INVOICE-{uuid.uuid4().hex[:12]}",
            description="Product used in invoice service tests",
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
    service = OrderService(
        db_session
    )

    order = service.create_order(
        OrderCreate(
            business_id=business_id,
            customer_id=customer_id,
            notes="Invoice service order",
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


def create_delivery_note(
    db_session: Session,
    business_id: int,
    order_id: int,
    order_line_id: int,
    *,
    quantity: Decimal = Decimal("4.000"),
    confirm: bool = True,
):
    service = DeliveryNoteService(
        db_session
    )

    delivery_note = (
        service.create_delivery_note(
            DeliveryNoteCreate(
                business_id=business_id,
                order_id=order_id,
                delivery_date=date(
                    2026,
                    10,
                    1,
                ),
                notes="Invoice service delivery note",
                lines=[
                    DeliveryNoteLineInput(
                        order_line_id=order_line_id,
                        quantity=quantity,
                        position=1,
                    )
                ],
            )
        )
    )

    if not confirm:
        return delivery_note

    confirmed = (
        service.confirm_delivery_note(
            delivery_note.id
        )
    )

    assert confirmed is not None

    return confirmed


def create_invoice_dependencies(
    db_session: Session,
    *,
    quantity: Decimal = Decimal("4.000"),
    unit_price: Decimal = Decimal("10.00"),
    tax_rate: Decimal = Decimal("21.00"),
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
        unit_price=unit_price,
        tax_rate=tax_rate,
    )

    order = create_confirmed_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    delivery_note = create_delivery_note(
        db_session,
        business.id,
        order.id,
        order.lines[0].id,
        quantity=quantity,
    )

    return (
        business,
        customer,
        product,
        order,
        delivery_note,
    )


def build_invoice_data(
    business_id: int,
    delivery_note_ids: list[int],
) -> InvoiceCreate:
    return InvoiceCreate(
        business_id=business_id,
        delivery_note_ids=delivery_note_ids,
        operation_date=date(
            2026,
            10,
            1,
        ),
        notes="Invoice service test",
    )


def test_create_invoice(
    db_session: Session,
):
    (
        business,
        customer,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    service = InvoiceService(
        db_session
    )

    invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [delivery_note.id],
        )
    )

    assert invoice is not None
    assert invoice.id is not None

    assert invoice.business_id == business.id
    assert invoice.customer_id == customer.id

    assert invoice.status == "DRAFT"
    assert invoice.invoice_type == "STANDARD"

    assert invoice.series is None
    assert invoice.number is None
    assert invoice.full_number is None
    assert invoice.issue_date is None
    assert invoice.issued_at is None

    assert len(invoice.lines) == 1
    assert len(invoice.delivery_notes) == 1

    assert (
        invoice.delivery_notes[0].delivery_note_id
        == delivery_note.id
    )


def test_create_invoice_snapshots_business_and_customer(
    db_session: Session,
):
    (
        business,
        customer,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    service = InvoiceService(
        db_session
    )

    invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [delivery_note.id],
        )
    )

    assert (
        invoice.issuer_legal_name
        == business.legal_name
    )
    assert (
        invoice.issuer_tax_id
        == business.tax_id
    )
    assert (
        invoice.issuer_address
        == business.address
    )
    assert (
        invoice.issuer_postal_code
        == business.postal_code
    )
    assert (
        invoice.issuer_city
        == business.city
    )
    assert (
        invoice.issuer_province
        == business.province
    )
    assert (
        invoice.issuer_country_code
        == business.country_code
    )

    assert (
        invoice.customer_legal_name
        == customer.legal_name
    )
    assert (
        invoice.customer_tax_id
        == customer.tax_id
    )
    assert (
        invoice.customer_address
        == customer.address
    )
    assert (
        invoice.customer_postal_code
        == customer.postal_code
    )
    assert (
        invoice.customer_city
        == customer.city
    )
    assert (
        invoice.customer_province
        == customer.province
    )
    assert (
        invoice.customer_country_code
        == customer.country_code
    )


def test_create_invoice_calculates_line_and_totals(
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session,
        quantity=Decimal("4.000"),
        unit_price=Decimal("12.50"),
        tax_rate=Decimal("10.00"),
    )

    service = InvoiceService(
        db_session
    )

    invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [delivery_note.id],
        )
    )

    assert len(invoice.lines) == 1

    line = invoice.lines[0]

    assert line.quantity == Decimal(
        "4.000"
    )

    assert line.unit_price == Decimal(
        "12.50"
    )

    assert line.tax_rate == Decimal(
        "10.00"
    )

    assert line.base_amount == Decimal(
        "50.00"
    )

    assert line.tax_amount == Decimal(
        "5.00"
    )

    assert line.total_amount == Decimal(
        "55.00"
    )

    assert invoice.subtotal == Decimal(
        "50.00"
    )

    assert invoice.tax_total == Decimal(
        "5.00"
    )

    assert invoice.total_amount == Decimal(
        "55.00"
    )


def test_create_invoice_with_missing_business(
    db_session: Session,
):
    service = InvoiceService(
        db_session
    )

    with pytest.raises(
        InvoiceBusinessNotFoundError
    ):
        service.create_invoice(
            InvoiceCreate(
                business_id=999999999,
                delivery_note_ids=[1],
            )
        )


def test_create_invoice_with_inactive_business(
    db_session: Session,
):
    business = create_business(
        db_session
    )

    business.is_active = False
    db_session.flush()

    service = InvoiceService(
        db_session
    )

    with pytest.raises(
        InvoiceBusinessInactiveError
    ):
        service.create_invoice(
            InvoiceCreate(
                business_id=business.id,
                delivery_note_ids=[1],
            )
        )


def test_create_invoice_rejects_duplicate_delivery_notes(
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    service = InvoiceService(
        db_session
    )

    with pytest.raises(
        InvoiceDuplicateDeliveryNoteError
    ):
        service.create_invoice(
            build_invoice_data(
                business.id,
                [
                    delivery_note.id,
                    delivery_note.id,
                ],
            )
        )


def test_create_invoice_rejects_missing_delivery_note(
    db_session: Session,
):
    business = create_business(
        db_session
    )

    service = InvoiceService(
        db_session
    )

    with pytest.raises(
        InvoiceDeliveryNoteNotFoundError
    ):
        service.create_invoice(
            build_invoice_data(
                business.id,
                [999999999],
            )
        )


def test_create_invoice_rejects_delivery_note_from_other_business(
    db_session: Session,
):
    own_business = create_business(
        db_session
    )

    (
        other_business,
        _,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    assert (
        own_business.id
        != other_business.id
    )

    service = InvoiceService(
        db_session
    )

    with pytest.raises(
        InvoiceDeliveryNoteTenantError
    ):
        service.create_invoice(
            build_invoice_data(
                own_business.id,
                [delivery_note.id],
            )
        )


def test_create_invoice_requires_confirmed_delivery_note(
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

    delivery_note = create_delivery_note(
        db_session,
        business.id,
        order.id,
        order.lines[0].id,
        confirm=False,
    )

    service = InvoiceService(
        db_session
    )

    with pytest.raises(
        InvoiceDeliveryNoteNotConfirmedError
    ):
        service.create_invoice(
            build_invoice_data(
                business.id,
                [delivery_note.id],
            )
        )


def test_create_invoice_rejects_mixed_customers(
    db_session: Session,
):
    business = create_business(
        db_session
    )

    first_customer = create_customer(
        db_session,
        business.id,
        legal_name="First Customer",
    )

    second_customer = create_customer(
        db_session,
        business.id,
        legal_name="Second Customer",
    )

    product = create_product(
        db_session,
        business.id,
    )

    first_order = create_confirmed_order(
        db_session,
        business.id,
        first_customer.id,
        product.id,
    )

    second_order = create_confirmed_order(
        db_session,
        business.id,
        second_customer.id,
        product.id,
    )

    first_delivery_note = (
        create_delivery_note(
            db_session,
            business.id,
            first_order.id,
            first_order.lines[0].id,
        )
    )

    second_delivery_note = (
        create_delivery_note(
            db_session,
            business.id,
            second_order.id,
            second_order.lines[0].id,
        )
    )

    service = InvoiceService(
        db_session
    )

    with pytest.raises(
        InvoiceMixedCustomerError
    ):
        service.create_invoice(
            build_invoice_data(
                business.id,
                [
                    first_delivery_note.id,
                    second_delivery_note.id,
                ],
            )
        )


def test_create_invoice_rejects_already_invoiced_delivery_note(
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    service = InvoiceService(
        db_session
    )

    service.create_invoice(
        build_invoice_data(
            business.id,
            [delivery_note.id],
        )
    )

    with pytest.raises(
        InvoiceDeliveryNoteAlreadyInvoicedError
    ):
        service.create_invoice(
            build_invoice_data(
                business.id,
                [delivery_note.id],
            )
        )


def test_get_invoice_by_id(
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    service = InvoiceService(
        db_session
    )

    created = service.create_invoice(
        build_invoice_data(
            business.id,
            [delivery_note.id],
        )
    )

    found = service.get_by_id(
        created.id
    )

    assert found is not None
    assert found.id == created.id
    assert len(found.lines) == 1
    assert len(found.delivery_notes) == 1


def test_list_invoices_by_business(
    db_session: Session,
):
    (
        first_business,
        _,
        _,
        _,
        first_delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    (
        second_business,
        _,
        _,
        _,
        second_delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    service = InvoiceService(
        db_session
    )

    first_invoice = (
        service.create_invoice(
            build_invoice_data(
                first_business.id,
                [first_delivery_note.id],
            )
        )
    )

    service.create_invoice(
        build_invoice_data(
            second_business.id,
            [second_delivery_note.id],
        )
    )

    invoices = (
        service.list_by_business_id(
            first_business.id
        )
    )

    assert [
        invoice.id
        for invoice in invoices
    ] == [
        first_invoice.id
    ]


def test_update_draft_invoice(
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
        unit_price=Decimal("10.00"),
    )

    second_product = create_product(
        db_session,
        business.id,
        name="Second Product",
        unit_price=Decimal("20.00"),
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
        create_delivery_note(
            db_session,
            business.id,
            first_order.id,
            first_order.lines[0].id,
            quantity=Decimal("2.000"),
        )
    )

    second_delivery_note = (
        create_delivery_note(
            db_session,
            business.id,
            second_order.id,
            second_order.lines[0].id,
            quantity=Decimal("3.000"),
        )
    )

    service = InvoiceService(
        db_session
    )

    invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [first_delivery_note.id],
        )
    )

    updated = service.update_invoice(
        invoice.id,
        InvoiceUpdate(
            delivery_note_ids=[
                second_delivery_note.id
            ],
            operation_date=date(
                2026,
                10,
                2,
            ),
            notes="Updated invoice",
        ),
    )

    assert updated is not None

    assert updated.notes == (
        "Updated invoice"
    )

    assert updated.operation_date == date(
        2026,
        10,
        2,
    )

    assert len(updated.lines) == 1

    assert (
        updated.lines[0].delivery_note_line_id
        == second_delivery_note.lines[0].id
    )

    assert updated.subtotal == Decimal(
        "60.00"
    )

    assert updated.tax_total == Decimal(
        "12.60"
    )

    assert updated.total_amount == Decimal(
        "72.60"
    )


def test_issue_invoice_assigns_number(
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    service = InvoiceService(
        db_session
    )

    invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [delivery_note.id],
        )
    )

    issued = service.issue_invoice(
        invoice.id,
        InvoiceIssue(
            series_code="F",
            issue_date=date(
                2026,
                10,
                1,
            ),
        ),
    )

    assert issued is not None

    assert issued.status == "ISSUED"

    assert issued.series == "F"
    assert issued.number == 1

    assert issued.full_number == (
        "F-000001"
    )

    assert issued.issue_date == date(
        2026,
        10,
        1,
    )

    assert issued.issued_at is not None
    assert issued.invoice_series_id is not None


def test_issue_invoice_normalizes_series_code(
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    service = InvoiceService(
        db_session
    )

    invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [delivery_note.id],
        )
    )

    issued = service.issue_invoice(
        invoice.id,
        InvoiceIssue(
            series_code=" f ",
            issue_date=date(
                2026,
                10,
                1,
            ),
        ),
    )

    assert issued is not None
    assert issued.series == "F"
    assert issued.full_number == (
        "F-000001"
    )


def test_invoice_numbers_are_sequential(
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

    first_delivery_note = (
        create_delivery_note(
            db_session,
            business.id,
            first_order.id,
            first_order.lines[0].id,
        )
    )

    second_delivery_note = (
        create_delivery_note(
            db_session,
            business.id,
            second_order.id,
            second_order.lines[0].id,
        )
    )

    service = InvoiceService(
        db_session
    )

    first_invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [first_delivery_note.id],
        )
    )

    first_issued = service.issue_invoice(
        first_invoice.id,
        InvoiceIssue(
            series_code="F",
            issue_date=date(
                2026,
                10,
                1,
            ),
        ),
    )

    second_invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [second_delivery_note.id],
        )
    )

    second_issued = service.issue_invoice(
        second_invoice.id,
        InvoiceIssue(
            series_code="F",
            issue_date=date(
                2026,
                10,
                1,
            ),
        ),
    )

    assert first_issued is not None
    assert second_issued is not None

    assert first_issued.number == 1
    assert first_issued.full_number == (
        "F-000001"
    )

    assert second_issued.number == 2
    assert second_issued.full_number == (
        "F-000002"
    )


def test_invoice_series_are_independent(
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

    first_delivery_note = (
        create_delivery_note(
            db_session,
            business.id,
            first_order.id,
            first_order.lines[0].id,
        )
    )

    second_delivery_note = (
        create_delivery_note(
            db_session,
            business.id,
            second_order.id,
            second_order.lines[0].id,
        )
    )

    service = InvoiceService(
        db_session
    )

    first_invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [first_delivery_note.id],
        )
    )

    second_invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [second_delivery_note.id],
        )
    )

    first_issued = service.issue_invoice(
        first_invoice.id,
        InvoiceIssue(
            series_code="F",
            issue_date=date(
                2026,
                10,
                1,
            ),
        ),
    )

    second_issued = service.issue_invoice(
        second_invoice.id,
        InvoiceIssue(
            series_code="G",
            issue_date=date(
                2026,
                10,
                1,
            ),
        ),
    )

    assert first_issued is not None
    assert second_issued is not None

    assert first_issued.full_number == (
        "F-000001"
    )

    assert second_issued.full_number == (
        "G-000001"
    )


def test_issued_invoice_cannot_be_updated(
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    service = InvoiceService(
        db_session
    )

    invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [delivery_note.id],
        )
    )

    service.issue_invoice(
        invoice.id,
        InvoiceIssue(
            series_code="F",
            issue_date=date(
                2026,
                10,
                1,
            ),
        ),
    )

    with pytest.raises(
        InvoiceNotEditableError
    ):
        service.update_invoice(
            invoice.id,
            InvoiceUpdate(
                notes="Forbidden edit",
            ),
        )


def test_invoice_cannot_be_issued_twice(
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    service = InvoiceService(
        db_session
    )

    invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [delivery_note.id],
        )
    )

    service.issue_invoice(
        invoice.id,
        InvoiceIssue(
            series_code="F",
            issue_date=date(
                2026,
                10,
                1,
            ),
        ),
    )

    with pytest.raises(
        InvoiceCannotIssueError
    ):
        service.issue_invoice(
            invoice.id,
            InvoiceIssue(
                series_code="F",
                issue_date=date(
                    2026,
                    10,
                    1,
                ),
            ),
        )


def test_invoice_cannot_be_issued_if_delivery_note_was_cancelled(
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    invoice_service = InvoiceService(
        db_session
    )

    invoice = (
        invoice_service.create_invoice(
            build_invoice_data(
                business.id,
                [delivery_note.id],
            )
        )
    )

    delivery_note_service = (
        DeliveryNoteService(
            db_session
        )
    )

    delivery_note_service.cancel_delivery_note(
        delivery_note.id
    )

    with pytest.raises(
        InvoiceDeliveryNoteNotConfirmedError
    ):
        invoice_service.issue_invoice(
            invoice.id,
            InvoiceIssue(
                series_code="F",
                issue_date=date(
                    2026,
                    10,
                    1,
                ),
            ),
        )


def test_create_invoice_without_commit_can_be_rolled_back(
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_invoice_dependencies(
        db_session
    )

    service = InvoiceService(
        db_session
    )

    invoice = service.create_invoice(
        build_invoice_data(
            business.id,
            [delivery_note.id],
        ),
        commit=False,
    )

    invoice_id = invoice.id

    db_session.rollback()

    assert (
        service.get_by_id(
            invoice_id
        )
        is None
    )