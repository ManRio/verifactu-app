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
from app.domain.order.schemas import OrderCreate, OrderLineInput
from app.domain.order.service import OrderService
from app.domain.product.schemas import ProductCreate
from app.domain.product.service import ProductService
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def create_business(
    db_session: Session,
):
    service = BusinessService(db_session)

    return service.create_business(
        BusinessCreate(
            legal_name="Delivery Note API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Albaran 1",
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
    service = UserService(db_session)

    return service.create_user(
        UserCreate(
            business_id=business_id,
            email=(
                email
                or f"delivery-user-{uuid.uuid4().hex[:12]}"
                "@example.com"
            ),
            password="password123",
            full_name="Delivery Note API User",
        )
    )


def get_auth_headers_for_business(
    client: TestClient,
    db_session: Session,
    business_id: int,
) -> dict[str, str]:
    email = (
        f"delivery-auth-{uuid.uuid4().hex[:12]}"
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

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


def create_customer(
    db_session: Session,
    business_id: int,
):
    service = CustomerService(db_session)

    return service.create_customer(
        CustomerCreate(
            business_id=business_id,
            tax_id=f"CUST-{uuid.uuid4().hex[:12]}",
            legal_name="Delivery Note API Customer",
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
    name: str = "Delivery Note API Product",
):
    service = ProductService(db_session)

    return service.create_product(
        ProductCreate(
            business_id=business_id,
            name=name,
            sku=f"DELIVERY-{uuid.uuid4().hex[:12]}",
            description="Product used in delivery note API tests",
            unit_price=Decimal("10.00"),
            tax_rate=Decimal("21.00"),
        )
    )


def create_order(
    db_session: Session,
    business_id: int,
    customer_id: int,
    product_id: int,
    *,
    quantity: Decimal = Decimal("10.000"),
    confirm: bool = True,
):
    service = OrderService(db_session)

    order = service.create_order(
        OrderCreate(
            business_id=business_id,
            customer_id=customer_id,
            notes="Delivery note API test order",
            lines=[
                OrderLineInput(
                    product_id=product_id,
                    quantity=quantity,
                    position=1,
                )
            ],
        )
    )

    if not confirm:
        return order

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
    confirm: bool = False,
):
    service = DeliveryNoteService(
        db_session
    )

    delivery_note = service.create_delivery_note(
        DeliveryNoteCreate(
            business_id=business_id,
            order_id=order_id,
            delivery_date=date(
                2026,
                9,
                29,
            ),
            notes="Delivery note API test",
            lines=[
                DeliveryNoteLineInput(
                    order_line_id=order_line_id,
                    quantity=quantity,
                    position=1,
                )
            ],
        )
    )

    if not confirm:
        return delivery_note

    confirmed = service.confirm_delivery_note(
        delivery_note.id
    )

    assert confirmed is not None

    return confirmed


def test_create_delivery_note_in_authenticated_business(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    customer = create_customer(
        db_session,
        business.id,
    )

    product = create_product(
        db_session,
        business.id,
        name="Caja de refrescos",
    )

    order = create_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    response = client.post(
        "/delivery-notes",
        headers=headers,
        json={
            "order_id": order.id,
            "delivery_date": "2026-09-29",
            "notes": "Entrega parcial",
            "lines": [
                {
                    "order_line_id": order.lines[0].id,
                    "quantity": "4.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["business_id"] == business.id
    assert data["order_id"] == order.id
    assert data["status"] == "DRAFT"
    assert data["delivery_date"] == "2026-09-29"
    assert data["notes"] == "Entrega parcial"
    assert len(data["lines"]) == 1

    line = data["lines"][0]

    assert line["order_line_id"] == order.lines[0].id
    assert line["description"] == "Caja de refrescos"
    assert Decimal(line["quantity"]) == Decimal("4.000")
    assert Decimal(line["unit_price"]) == Decimal("10.00")
    assert Decimal(line["tax_rate"]) == Decimal("21.00")


def test_create_delivery_note_does_not_accept_business_id(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    other_business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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

    response = client.post(
        "/delivery-notes",
        headers=headers,
        json={
            "business_id": other_business.id,
            "order_id": order.id,
            "delivery_date": "2026-09-29",
            "lines": [
                {
                    "order_line_id": order.lines[0].id,
                    "quantity": "1.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 422


def test_create_delivery_note_without_authentication_returns_401(
    client: TestClient,
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

    response = client.post(
        "/delivery-notes",
        json={
            "order_id": order.id,
            "delivery_date": "2026-09-29",
            "lines": [
                {
                    "order_line_id": order.lines[0].id,
                    "quantity": "1.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 401


def test_create_delivery_note_with_other_business_order_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(
        db_session
    )

    other_business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    customer = create_customer(
        db_session,
        other_business.id,
    )

    product = create_product(
        db_session,
        other_business.id,
    )

    order = create_order(
        db_session,
        other_business.id,
        customer.id,
        product.id,
    )

    response = client.post(
        "/delivery-notes",
        headers=headers,
        json={
            "order_id": order.id,
            "delivery_date": "2026-09-29",
            "lines": [
                {
                    "order_line_id": order.lines[0].id,
                    "quantity": "1.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Order not found"
    }


def test_create_delivery_note_requires_confirmed_order(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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
        confirm=False,
    )

    response = client.post(
        "/delivery-notes",
        headers=headers,
        json={
            "order_id": order.id,
            "delivery_date": "2026-09-29",
            "lines": [
                {
                    "order_line_id": order.lines[0].id,
                    "quantity": "1.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Order must be confirmed"
    }


def test_create_delivery_note_rejects_line_from_other_order(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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

    response = client.post(
        "/delivery-notes",
        headers=headers,
        json={
            "order_id": first_order.id,
            "delivery_date": "2026-09-29",
            "lines": [
                {
                    "order_line_id": second_order.lines[0].id,
                    "quantity": "1.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Order line not found"
    }


def test_create_delivery_note_rejects_quantity_above_ordered(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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
        quantity=Decimal("10.000"),
    )

    response = client.post(
        "/delivery-notes",
        headers=headers,
        json={
            "order_id": order.id,
            "delivery_date": "2026-09-29",
            "lines": [
                {
                    "order_line_id": order.lines[0].id,
                    "quantity": "11.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Delivery quantity exceeds ordered quantity"
    }


def test_list_delivery_notes_returns_only_authenticated_business(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(
        db_session
    )

    other_business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    own_customer = create_customer(
        db_session,
        own_business.id,
    )

    other_customer = create_customer(
        db_session,
        other_business.id,
    )

    own_product = create_product(
        db_session,
        own_business.id,
    )

    other_product = create_product(
        db_session,
        other_business.id,
    )

    own_order = create_order(
        db_session,
        own_business.id,
        own_customer.id,
        own_product.id,
    )

    other_order = create_order(
        db_session,
        other_business.id,
        other_customer.id,
        other_product.id,
    )

    own_note = create_delivery_note(
        db_session,
        own_business.id,
        own_order.id,
        own_order.lines[0].id,
    )

    create_delivery_note(
        db_session,
        other_business.id,
        other_order.id,
        other_order.lines[0].id,
    )

    response = client.get(
        "/delivery-notes",
        headers=headers,
    )

    assert response.status_code == 200

    delivery_notes = response.json()

    returned_ids = {
        delivery_note["id"]
        for delivery_note in delivery_notes
    }

    assert own_note.id in returned_ids

    assert all(
        delivery_note["business_id"]
        == own_business.id
        for delivery_note in delivery_notes
    )


def test_list_delivery_notes_without_authentication_returns_401(
    client: TestClient,
):
    response = client.get(
        "/delivery-notes"
    )

    assert response.status_code == 401


def test_get_own_business_delivery_note(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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

    response = client.get(
        f"/delivery-notes/{delivery_note.id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == delivery_note.id
    assert data["business_id"] == business.id
    assert data["order_id"] == order.id
    assert len(data["lines"]) == 1


def test_get_other_business_delivery_note_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(
        db_session
    )

    other_business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    customer = create_customer(
        db_session,
        other_business.id,
    )

    product = create_product(
        db_session,
        other_business.id,
    )

    order = create_order(
        db_session,
        other_business.id,
        customer.id,
        product.id,
    )

    delivery_note = create_delivery_note(
        db_session,
        other_business.id,
        order.id,
        order.lines[0].id,
    )

    response = client.get(
        f"/delivery-notes/{delivery_note.id}",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource not found"
    }


def test_get_nonexistent_delivery_note_returns_404(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    response = client.get(
        "/delivery-notes/999999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_update_draft_delivery_note(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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

    response = client.patch(
        f"/delivery-notes/{delivery_note.id}",
        headers=headers,
        json={
            "delivery_date": "2026-09-30",
            "notes": "Entrega modificada",
            "lines": [
                {
                    "order_line_id": order.lines[0].id,
                    "quantity": "3.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "DRAFT"
    assert data["delivery_date"] == "2026-09-30"
    assert data["notes"] == "Entrega modificada"
    assert Decimal(
        data["lines"][0]["quantity"]
    ) == Decimal("3.000")


def test_update_delivery_note_rejects_business_id(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    other_business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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

    response = client.patch(
        f"/delivery-notes/{delivery_note.id}",
        headers=headers,
        json={
            "business_id": other_business.id,
        },
    )

    assert response.status_code == 422


def test_confirm_delivery_note(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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

    response = client.patch(
        f"/delivery-notes/{delivery_note.id}/confirm",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "CONFIRMED"
    assert data["confirmed_at"] is not None


def test_confirmed_delivery_note_cannot_be_updated(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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
        confirm=True,
    )

    response = client.patch(
        f"/delivery-notes/{delivery_note.id}",
        headers=headers,
        json={
            "notes": "Forbidden edit",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": "Only draft delivery notes can be edited"
    }


def test_confirm_delivery_note_rejects_quantity_above_remaining(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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
        quantity=Decimal("10.000"),
    )

    create_delivery_note(
        db_session,
        business.id,
        order.id,
        order.lines[0].id,
        quantity=Decimal("6.000"),
        confirm=True,
    )

    second = create_delivery_note(
        db_session,
        business.id,
        order.id,
        order.lines[0].id,
        quantity=Decimal("5.000"),
    )

    response = client.patch(
        f"/delivery-notes/{second.id}/confirm",
        headers=headers,
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": "Delivery quantity exceeds remaining quantity"
    }


def test_cancel_draft_delivery_note(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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

    response = client.patch(
        f"/delivery-notes/{delivery_note.id}/cancel",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_cancel_confirmed_delivery_note(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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
        confirm=True,
    )

    response = client.patch(
        f"/delivery-notes/{delivery_note.id}/cancel",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_cancelled_delivery_note_cannot_be_cancelled_again(
    client: TestClient,
    db_session: Session,
):
    business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
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

    service = DeliveryNoteService(
        db_session
    )

    service.cancel_delivery_note(
        delivery_note.id
    )

    response = client.patch(
        f"/delivery-notes/{delivery_note.id}/cancel",
        headers=headers,
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": "Delivery note cannot be cancelled"
    }


def test_confirm_other_business_delivery_note_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(
        db_session
    )

    other_business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    customer = create_customer(
        db_session,
        other_business.id,
    )

    product = create_product(
        db_session,
        other_business.id,
    )

    order = create_order(
        db_session,
        other_business.id,
        customer.id,
        product.id,
    )

    delivery_note = create_delivery_note(
        db_session,
        other_business.id,
        order.id,
        order.lines[0].id,
    )

    response = client.patch(
        f"/delivery-notes/{delivery_note.id}/confirm",
        headers=headers,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Resource not found"
    }


def test_cancel_other_business_delivery_note_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(
        db_session
    )

    other_business = create_business(
        db_session
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    customer = create_customer(
        db_session,
        other_business.id,
    )

    product = create_product(
        db_session,
        other_business.id,
    )

    order = create_order(
        db_session,
        other_business.id,
        customer.id,
        product.id,
    )

    delivery_note = create_delivery_note(
        db_session,
        other_business.id,
        order.id,
        order.lines[0].id,
    )

    response = client.patch(
        f"/delivery-notes/{delivery_note.id}/cancel",
        headers=headers,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Resource not found"
    }


def test_confirm_delivery_note_without_authentication_returns_401(
    client: TestClient,
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

    response = client.patch(
        f"/delivery-notes/{delivery_note.id}/confirm"
    )

    assert response.status_code == 401


def test_cancel_delivery_note_without_authentication_returns_401(
    client: TestClient,
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

    response = client.patch(
        f"/delivery-notes/{delivery_note.id}/cancel"
    )

    assert response.status_code == 401