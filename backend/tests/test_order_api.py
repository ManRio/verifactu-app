import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import BusinessService
from app.domain.customer.schemas import CustomerCreate
from app.domain.customer.service import CustomerService
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
            legal_name="Order API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Pedido 1",
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
                or f"order-user-{uuid.uuid4().hex[:12]}"
                "@example.com"
            ),
            password="password123",
            full_name="Order API User",
        )
    )


def get_auth_headers_for_business(
    client: TestClient,
    db_session: Session,
    business_id: int,
) -> dict[str, str]:
    email = (
        f"order-auth-{uuid.uuid4().hex[:12]}"
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
    *,
    legal_name: str = "Order API Customer",
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
    name: str = "Order API Product",
    unit_price: Decimal = Decimal("10.00"),
    tax_rate: Decimal = Decimal("21.00"),
):
    service = ProductService(db_session)

    return service.create_product(
        ProductCreate(
            business_id=business_id,
            name=name,
            sku=f"ORDER-{uuid.uuid4().hex[:12]}",
            description="Product used in order API tests",
            unit_price=unit_price,
            tax_rate=tax_rate,
        )
    )


def create_order(
    db_session: Session,
    business_id: int,
    customer_id: int,
    product_id: int,
):
    service = OrderService(db_session)

    return service.create_order(
        OrderCreate(
            business_id=business_id,
            customer_id=customer_id,
            notes="Order API test",
            lines=[
                OrderLineInput(
                    product_id=product_id,
                    quantity=Decimal("2.000"),
                    position=1,
                )
            ],
        )
    )


def test_create_order_in_authenticated_business(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

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
        unit_price=Decimal("18.50"),
        tax_rate=Decimal("21.00"),
    )

    response = client.post(
        "/orders",
        headers=headers,
        json={
            "customer_id": customer.id,
            "notes": "Entregar por la mañana",
            "lines": [
                {
                    "product_id": product.id,
                    "quantity": "2.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["business_id"] == business.id
    assert data["customer_id"] == customer.id
    assert data["status"] == "DRAFT"
    assert data["notes"] == "Entregar por la mañana"

    assert Decimal(data["subtotal"]) == Decimal("37.00")
    assert Decimal(data["tax_total"]) == Decimal("7.77")
    assert Decimal(data["total_amount"]) == Decimal("44.77")

    assert len(data["lines"]) == 1

    line = data["lines"][0]

    assert line["product_id"] == product.id
    assert line["description"] == "Caja de refrescos"
    assert Decimal(line["quantity"]) == Decimal("2.000")
    assert Decimal(line["unit_price"]) == Decimal("18.50")


def test_create_order_does_not_accept_business_id(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(db_session)
    other_business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    customer = create_customer(
        db_session,
        own_business.id,
    )

    product = create_product(
        db_session,
        own_business.id,
    )

    response = client.post(
        "/orders",
        headers=headers,
        json={
            "business_id": other_business.id,
            "customer_id": customer.id,
            "lines": [
                {
                    "product_id": product.id,
                    "quantity": "1.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 422


def test_create_order_without_authentication_returns_401(
    client: TestClient,
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

    response = client.post(
        "/orders",
        json={
            "customer_id": customer.id,
            "lines": [
                {
                    "product_id": product.id,
                    "quantity": "1.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 401


def test_create_order_with_customer_from_other_business_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(db_session)
    other_business = create_business(db_session)

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
        own_business.id,
    )

    response = client.post(
        "/orders",
        headers=headers,
        json={
            "customer_id": customer.id,
            "lines": [
                {
                    "product_id": product.id,
                    "quantity": "1.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Customer not found"
    }


def test_create_order_with_product_from_other_business_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(db_session)
    other_business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        own_business.id,
    )

    customer = create_customer(
        db_session,
        own_business.id,
    )

    product = create_product(
        db_session,
        other_business.id,
    )

    response = client.post(
        "/orders",
        headers=headers,
        json={
            "customer_id": customer.id,
            "lines": [
                {
                    "product_id": product.id,
                    "quantity": "1.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Product not found"
    }


def test_create_order_with_inactive_customer_returns_409(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

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

    customer.is_active = False
    db_session.flush()

    response = client.post(
        "/orders",
        headers=headers,
        json={
            "customer_id": customer.id,
            "lines": [
                {
                    "product_id": product.id,
                    "quantity": "1.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Customer is inactive"
    }


def test_create_order_with_inactive_product_returns_409(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

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

    product.is_active = False
    db_session.flush()

    response = client.post(
        "/orders",
        headers=headers,
        json={
            "customer_id": customer.id,
            "lines": [
                {
                    "product_id": product.id,
                    "quantity": "1.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Product is inactive"
    }


def test_create_order_rejects_duplicate_positions(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

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

    response = client.post(
        "/orders",
        headers=headers,
        json={
            "customer_id": customer.id,
            "lines": [
                {
                    "product_id": first_product.id,
                    "quantity": "1.000",
                    "position": 1,
                },
                {
                    "product_id": second_product.id,
                    "quantity": "1.000",
                    "position": 1,
                },
            ],
        },
    )

    assert response.status_code == 422


def test_list_orders_returns_only_authenticated_business(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(db_session)
    other_business = create_business(db_session)

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

    response = client.get(
        "/orders",
        headers=headers,
    )

    assert response.status_code == 200

    orders = response.json()

    returned_ids = {
        order["id"]
        for order in orders
    }

    assert own_order.id in returned_ids
    assert other_order.id not in returned_ids

    assert all(
        order["business_id"] == own_business.id
        for order in orders
    )


def test_list_orders_without_authentication_returns_401(
    client: TestClient,
):
    response = client.get(
        "/orders"
    )

    assert response.status_code == 401


def test_get_own_business_order(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

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

    response = client.get(
        f"/orders/{order.id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order.id
    assert data["business_id"] == business.id
    assert len(data["lines"]) == 1


def test_get_other_business_order_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(db_session)
    other_business = create_business(db_session)

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

    response = client.get(
        f"/orders/{order.id}",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource not found"
    }


def test_get_nonexistent_order_returns_404(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    response = client.get(
        "/orders/999999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_update_draft_order(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

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
        name="Updated Product",
        unit_price=Decimal("5.00"),
        tax_rate=Decimal("10.00"),
    )

    order = create_order(
        db_session,
        business.id,
        customer.id,
        first_product.id,
    )

    response = client.patch(
        f"/orders/{order.id}",
        headers=headers,
        json={
            "notes": "Updated notes",
            "lines": [
                {
                    "product_id": second_product.id,
                    "quantity": "3.000",
                    "position": 1,
                }
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["notes"] == "Updated notes"
    assert data["status"] == "DRAFT"
    assert len(data["lines"]) == 1

    line = data["lines"][0]

    assert line["product_id"] == second_product.id
    assert line["description"] == "Updated Product"

    assert Decimal(data["subtotal"]) == Decimal("15.00")
    assert Decimal(data["tax_total"]) == Decimal("1.50")
    assert Decimal(data["total_amount"]) == Decimal("16.50")


def test_update_other_business_order_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(db_session)
    other_business = create_business(db_session)

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

    response = client.patch(
        f"/orders/{order.id}",
        headers=headers,
        json={
            "notes": "Forbidden update",
        },
    )

    assert response.status_code == 404


def test_update_order_rejects_business_id(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)
    other_business = create_business(db_session)

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

    response = client.patch(
        f"/orders/{order.id}",
        headers=headers,
        json={
            "business_id": other_business.id,
        },
    )

    assert response.status_code == 422


def test_update_order_rejects_status(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

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

    response = client.patch(
        f"/orders/{order.id}",
        headers=headers,
        json={
            "status": "CONFIRMED",
        },
    )

    assert response.status_code == 422


def test_confirm_order(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

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

    response = client.patch(
        f"/orders/{order.id}/confirm",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "CONFIRMED"
    assert data["confirmed_at"] is not None


def test_confirmed_order_cannot_be_updated(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

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

    service = OrderService(db_session)
    service.confirm_order(order.id)

    response = client.patch(
        f"/orders/{order.id}",
        headers=headers,
        json={
            "notes": "Forbidden edit",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Only draft orders can be edited"
    }


def test_confirmed_order_cannot_be_confirmed_again(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

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

    service = OrderService(db_session)
    service.confirm_order(order.id)

    response = client.patch(
        f"/orders/{order.id}/confirm",
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Order cannot be confirmed"
    }


def test_confirm_other_business_order_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(db_session)
    other_business = create_business(db_session)

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

    response = client.patch(
        f"/orders/{order.id}/confirm",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource not found"
    }


def test_cancel_draft_order(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

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

    response = client.patch(
        f"/orders/{order.id}/cancel",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_cancel_confirmed_order(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

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

    service = OrderService(db_session)
    service.confirm_order(order.id)

    response = client.patch(
        f"/orders/{order.id}/cancel",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_cancelled_order_cannot_be_cancelled_again(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

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

    service = OrderService(db_session)
    service.cancel_order(order.id)

    response = client.patch(
        f"/orders/{order.id}/cancel",
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Order cannot be cancelled"
    }


def test_cancel_other_business_order_returns_404(
    client: TestClient,
    db_session: Session,
):
    own_business = create_business(db_session)
    other_business = create_business(db_session)

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

    response = client.patch(
        f"/orders/{order.id}/cancel",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource not found"
    }


def test_confirm_order_without_authentication_returns_401(
    client: TestClient,
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

    order = create_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    response = client.patch(
        f"/orders/{order.id}/confirm"
    )

    assert response.status_code == 401


def test_cancel_order_without_authentication_returns_401(
    client: TestClient,
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

    order = create_order(
        db_session,
        business.id,
        customer.id,
        product.id,
    )

    response = client.patch(
        f"/orders/{order.id}/cancel"
    )

    assert response.status_code == 401