import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import BusinessService
from app.domain.customer.schemas import CustomerCreate
from app.domain.customer.service import CustomerService
from app.domain.delivery_note.schemas import (
    DeliveryNoteCreate,
    DeliveryNoteLineInput,
)
from app.domain.delivery_note.service import DeliveryNoteService
from app.domain.invoice.schemas import InvoiceCreate
from app.domain.invoice.service import InvoiceService
from app.domain.order.schemas import (
    OrderCreate,
    OrderLineInput,
)
from app.domain.order.service import OrderService
from app.domain.product.schemas import ProductCreate
from app.domain.product.service import ProductService
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def create_business(
    db_session: Session,
):
    service = BusinessService(
        db_session
    )

    return service.create_business(
        BusinessCreate(
            legal_name="Invoice API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Factura 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )


def create_user(
    db_session: Session,
    business_id: int,
    *,
    email: str | None = None,
):
    service = UserService(
        db_session
    )

    return service.create_user(
        UserCreate(
            business_id=business_id,
            email=(
                email
                or f"invoice-user-{uuid.uuid4().hex[:12]}"
                "@example.com"
            ),
            password="password123",
            full_name="Invoice API User",
        )
    )


def get_auth_headers_for_business(
    client: TestClient,
    db_session: Session,
    business_id: int,
) -> dict[str, str]:
    email = (
        f"invoice-auth-{uuid.uuid4().hex[:12]}"
        "@example.com"
    )

    password = "password123"

    create_user(
        db_session,
        business_id,
        email=email,
    )

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    token = response.json()[
        "access_token"
    ]

    return {
        "Authorization": f"Bearer {token}",
    }


def create_customer(
    db_session: Session,
    business_id: int,
    *,
    legal_name: str = "Invoice API Customer",
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
    name: str = "Invoice API Product",
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
                "Product used in invoice API tests"
            ),
            unit_price=Decimal("10.00"),
            tax_rate=Decimal("21.00"),
        )
    )


def create_order(
    db_session: Session,
    business_id: int,
    customer_id: int,
    product_id: int,
):
    service = OrderService(
        db_session
    )

    order = service.create_order(
        OrderCreate(
            business_id=business_id,
            customer_id=customer_id,
            notes="Invoice API order",
            lines=[
                OrderLineInput(
                    product_id=product_id,
                    quantity=Decimal(
                        "10.000"
                    ),
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
    quantity: Decimal = Decimal(
        "4.000"
    ),
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
                notes="Invoice API delivery note",
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


def create_dependencies(
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

    order = create_order(
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
    )

    return (
        business,
        customer,
        product,
        order,
        delivery_note,
    )


def create_invoice(
    db_session: Session,
    business_id: int,
    delivery_note_ids: list[int],
):
    service = InvoiceService(
        db_session
    )

    return service.create_invoice(
        InvoiceCreate(
            business_id=business_id,
            delivery_note_ids=(
                delivery_note_ids
            ),
            operation_date=date(
                2026,
                10,
                1,
            ),
            notes="Invoice API test",
        )
    )


def test_create_invoice_in_authenticated_business(
    client: TestClient,
    db_session: Session,
):
    (
        business,
        customer,
        _,
        _,
        delivery_note,
    ) = create_dependencies(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            business.id,
        )
    )

    response = client.post(
        "/invoices",
        headers=headers,
        json={
            "delivery_note_ids": [
                delivery_note.id
            ],
            "operation_date": (
                "2026-10-01"
            ),
            "notes": "Factura octubre",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["business_id"] == (
        business.id
    )

    assert data["customer_id"] == (
        customer.id
    )

    assert data["status"] == "DRAFT"
    assert data["invoice_type"] == (
        "STANDARD"
    )

    assert data["series"] is None
    assert data["number"] is None
    assert data["full_number"] is None

    assert len(data["lines"]) == 1

    assert (
        data["delivery_notes"][0][
            "delivery_note_id"
        ]
        == delivery_note.id
    )

    assert Decimal(
        data["subtotal"]
    ) == Decimal("40.00")

    assert Decimal(
        data["tax_total"]
    ) == Decimal("8.40")

    assert Decimal(
        data["total_amount"]
    ) == Decimal("48.40")


def test_create_invoice_does_not_accept_business_id(
    client: TestClient,
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_dependencies(
        db_session
    )

    other_business = create_business(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            business.id,
        )
    )

    response = client.post(
        "/invoices",
        headers=headers,
        json={
            "business_id": (
                other_business.id
            ),
            "delivery_note_ids": [
                delivery_note.id
            ],
        },
    )

    assert response.status_code == 422


def test_create_invoice_without_authentication_returns_401(
    client: TestClient,
    db_session: Session,
):
    (
        _,
        _,
        _,
        _,
        delivery_note,
    ) = create_dependencies(
        db_session
    )

    response = client.post(
        "/invoices",
        json={
            "delivery_note_ids": [
                delivery_note.id
            ],
        },
    )

    assert response.status_code == 401


def test_create_invoice_with_other_business_delivery_note_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(
        db_session
    )

    (
        _,
        _,
        _,
        _,
        other_delivery_note,
    ) = create_dependencies(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            own_business.id,
        )
    )

    response = client.post(
        "/invoices",
        headers=headers,
        json={
            "delivery_note_ids": [
                other_delivery_note.id
            ],
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Delivery note not found"
        )
    }


def test_create_invoice_requires_confirmed_delivery_note(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            business.id,
        )
    )

    customer = create_customer(
        db_session,
        business.id,
    )

    product = create_product(
        db_session,
        business.id,
    )

    order = create_order(
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

    response = client.post(
        "/invoices",
        headers=headers,
        json={
            "delivery_note_ids": [
                delivery_note.id
            ],
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Delivery note must be confirmed"
        )
    }


def test_create_invoice_rejects_already_invoiced_delivery_note(
    client: TestClient,
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_dependencies(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            business.id,
        )
    )

    create_invoice(
        db_session,
        business.id,
        [delivery_note.id],
    )

    response = client.post(
        "/invoices",
        headers=headers,
        json={
            "delivery_note_ids": [
                delivery_note.id
            ],
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Delivery note is already invoiced"
        )
    }


def test_create_invoice_rejects_mixed_customers(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            business.id,
        )
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

    first_order = create_order(
        db_session,
        business.id,
        first_customer.id,
        product.id,
    )

    second_order = create_order(
        db_session,
        business.id,
        second_customer.id,
        product.id,
    )

    first_note = create_delivery_note(
        db_session,
        business.id,
        first_order.id,
        first_order.lines[0].id,
    )

    second_note = create_delivery_note(
        db_session,
        business.id,
        second_order.id,
        second_order.lines[0].id,
    )

    response = client.post(
        "/invoices",
        headers=headers,
        json={
            "delivery_note_ids": [
                first_note.id,
                second_note.id,
            ],
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "All delivery notes must belong "
            "to the same customer"
        )
    }


def test_list_invoices_returns_only_authenticated_business(
    client: TestClient,
    db_session: Session,
):
    (
        own_business,
        _,
        _,
        _,
        own_note,
    ) = create_dependencies(
        db_session
    )

    (
        other_business,
        _,
        _,
        _,
        other_note,
    ) = create_dependencies(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            own_business.id,
        )
    )

    own_invoice = create_invoice(
        db_session,
        own_business.id,
        [own_note.id],
    )

    create_invoice(
        db_session,
        other_business.id,
        [other_note.id],
    )

    response = client.get(
        "/invoices",
        headers=headers,
    )

    assert response.status_code == 200

    invoices = response.json()

    returned_ids = {
        invoice["id"]
        for invoice in invoices
    }

    assert own_invoice.id in returned_ids

    assert all(
        invoice["business_id"]
        == own_business.id
        for invoice in invoices
    )


def test_list_invoices_without_authentication_returns_401(
    client: TestClient,
):
    response = client.get(
        "/invoices"
    )

    assert response.status_code == 401


def test_get_own_business_invoice(
    client: TestClient,
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_dependencies(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            business.id,
        )
    )

    invoice = create_invoice(
        db_session,
        business.id,
        [delivery_note.id],
    )

    response = client.get(
        f"/invoices/{invoice.id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == invoice.id

    assert data["business_id"] == (
        business.id
    )

    assert len(data["lines"]) == 1

    assert len(
        data["delivery_notes"]
    ) == 1


def test_get_other_business_invoice_returns_404(
    client: TestClient,
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
    ) = create_dependencies(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            own_business.id,
        )
    )

    invoice = create_invoice(
        db_session,
        other_business.id,
        [delivery_note.id],
    )

    response = client.get(
        f"/invoices/{invoice.id}",
        headers=headers,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Resource not found"
    }


def test_get_nonexistent_invoice_returns_404(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            business.id,
        )
    )

    response = client.get(
        "/invoices/999999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_update_draft_invoice(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            business.id,
        )
    )

    customer = create_customer(
        db_session,
        business.id,
    )

    product = create_product(
        db_session,
        business.id,
    )

    first_order = create_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    second_order = create_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    first_note = create_delivery_note(
        db_session,
        business.id,
        first_order.id,
        first_order.lines[0].id,
        quantity=Decimal("2.000"),
    )

    second_note = create_delivery_note(
        db_session,
        business.id,
        second_order.id,
        second_order.lines[0].id,
        quantity=Decimal("3.000"),
    )

    invoice = create_invoice(
        db_session,
        business.id,
        [first_note.id],
    )

    response = client.patch(
        f"/invoices/{invoice.id}",
        headers=headers,
        json={
            "delivery_note_ids": [
                second_note.id
            ],
            "operation_date": (
                "2026-10-02"
            ),
            "notes": (
                "Factura modificada"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "DRAFT"

    assert data["operation_date"] == (
        "2026-10-02"
    )

    assert data["notes"] == (
        "Factura modificada"
    )

    assert (
        data["delivery_notes"][0][
            "delivery_note_id"
        ]
        == second_note.id
    )

    assert Decimal(
        data["subtotal"]
    ) == Decimal("30.00")

    assert Decimal(
        data["total_amount"]
    ) == Decimal("36.30")


def test_update_invoice_rejects_business_id(
    client: TestClient,
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_dependencies(
        db_session
    )

    other_business = create_business(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            business.id,
        )
    )

    invoice = create_invoice(
        db_session,
        business.id,
        [delivery_note.id],
    )

    response = client.patch(
        f"/invoices/{invoice.id}",
        headers=headers,
        json={
            "business_id": (
                other_business.id
            ),
        },
    )

    assert response.status_code == 422


def test_issue_invoice(
    client: TestClient,
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_dependencies(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            business.id,
        )
    )

    invoice = create_invoice(
        db_session,
        business.id,
        [delivery_note.id],
    )

    response = client.patch(
        f"/invoices/{invoice.id}/issue",
        headers=headers,
        json={
            "series_code": "F",
            "issue_date": "2026-10-01",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ISSUED"

    assert data["series"] == "F"
    assert data["number"] == 1

    assert data["full_number"] == (
        "F-000001"
    )

    assert data["issue_date"] == (
        "2026-10-01"
    )

    assert data["issued_at"] is not None


def test_issued_invoice_cannot_be_updated(
    client: TestClient,
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_dependencies(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            business.id,
        )
    )

    invoice = create_invoice(
        db_session,
        business.id,
        [delivery_note.id],
    )

    issue_response = client.patch(
        f"/invoices/{invoice.id}/issue",
        headers=headers,
        json={
            "series_code": "F",
            "issue_date": "2026-10-01",
        },
    )

    assert (
        issue_response.status_code
        == 200
    )

    response = client.patch(
        f"/invoices/{invoice.id}",
        headers=headers,
        json={
            "notes": "Forbidden edit",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Only draft invoices can be edited"
        )
    }


def test_invoice_cannot_be_issued_twice(
    client: TestClient,
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_dependencies(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            business.id,
        )
    )

    invoice = create_invoice(
        db_session,
        business.id,
        [delivery_note.id],
    )

    first_response = client.patch(
        f"/invoices/{invoice.id}/issue",
        headers=headers,
        json={
            "series_code": "F",
            "issue_date": "2026-10-01",
        },
    )

    assert (
        first_response.status_code
        == 200
    )

    second_response = client.patch(
        f"/invoices/{invoice.id}/issue",
        headers=headers,
        json={
            "series_code": "F",
            "issue_date": "2026-10-01",
        },
    )

    assert (
        second_response.status_code
        == 409
    )

    assert second_response.json() == {
        "detail": (
            "Invoice cannot be issued"
        )
    }


def test_issue_other_business_invoice_returns_404(
    client: TestClient,
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
    ) = create_dependencies(
        db_session
    )

    headers = (
        get_auth_headers_for_business(
            client,
            db_session,
            own_business.id,
        )
    )

    invoice = create_invoice(
        db_session,
        other_business.id,
        [delivery_note.id],
    )

    response = client.patch(
        f"/invoices/{invoice.id}/issue",
        headers=headers,
        json={
            "series_code": "F",
            "issue_date": "2026-10-01",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Resource not found"
    }


def test_issue_invoice_without_authentication_returns_401(
    client: TestClient,
    db_session: Session,
):
    (
        business,
        _,
        _,
        _,
        delivery_note,
    ) = create_dependencies(
        db_session
    )

    invoice = create_invoice(
        db_session,
        business.id,
        [delivery_note.id],
    )

    response = client.patch(
        f"/invoices/{invoice.id}/issue",
        json={
            "series_code": "F",
            "issue_date": "2026-10-01",
        },
    )

    assert response.status_code == 401