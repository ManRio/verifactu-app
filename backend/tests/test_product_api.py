import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import BusinessService
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
            legal_name="Product API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Producto 1",
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
                or f"product-user-{uuid.uuid4().hex[:12]}"
                "@example.com"
            ),
            password="password123",
            full_name="Product API User",
        )
    )


def get_auth_headers_for_business(
    client: TestClient,
    db_session: Session,
    business_id: int,
) -> dict[str, str]:
    email = (
        f"product-auth-{uuid.uuid4().hex[:12]}"
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


def create_product(
    db_session: Session,
    business_id: int,
    *,
    name: str = "Test Product",
    sku: str | None = None,
    unit_price: Decimal = Decimal("10.00"),
    tax_rate: Decimal = Decimal("21.00"),
):
    service = ProductService(db_session)

    return service.create_product(
        ProductCreate(
            business_id=business_id,
            name=name,
            sku=(
                sku
                if sku is not None
                else f"SKU-{uuid.uuid4().hex[:12]}"
            ),
            description="Test product description",
            unit_price=unit_price,
            tax_rate=tax_rate,
        )
    )


def test_create_product_in_authenticated_business(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    response = client.post(
        "/products",
        headers=headers,
        json={
            "name": "Mechanical Keyboard",
            "sku": "KEYBOARD-001",
            "description": "Mechanical keyboard",
            "unit_price": "59.90",
            "tax_rate": "21.00",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["business_id"] == business.id
    assert data["name"] == "Mechanical Keyboard"
    assert data["sku"] == "KEYBOARD-001"
    assert data["description"] == "Mechanical keyboard"

    assert Decimal(
        str(data["unit_price"])
    ) == Decimal("59.90")

    assert Decimal(
        str(data["tax_rate"])
    ) == Decimal("21.00")

    assert data["is_active"] is True


def test_create_product_does_not_accept_business_id(
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

    response = client.post(
        "/products",
        headers=headers,
        json={
            "business_id": other_business.id,
            "name": "Cross Tenant Product",
            "sku": "CROSS-001",
            "unit_price": "10.00",
            "tax_rate": "21.00",
        },
    )

    assert response.status_code == 422


def test_create_product_without_authentication_returns_401(
    client: TestClient,
):
    response = client.post(
        "/products",
        json={
            "name": "Unauthenticated Product",
            "sku": "NOAUTH-001",
            "unit_price": "10.00",
            "tax_rate": "21.00",
        },
    )

    assert response.status_code == 401


def test_create_duplicate_sku_in_same_business_returns_409(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    create_product(
        db_session,
        business.id,
        sku="DUPLICATE-001",
    )

    response = client.post(
        "/products",
        headers=headers,
        json={
            "name": "Duplicate Product",
            "sku": "DUPLICATE-001",
            "unit_price": "20.00",
            "tax_rate": "21.00",
        },
    )

    assert response.status_code == 409


def test_same_sku_is_allowed_in_different_businesses(
    client: TestClient,
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    create_product(
        db_session,
        first_business.id,
        sku="SHARED-001",
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        second_business.id,
    )

    response = client.post(
        "/products",
        headers=headers,
        json={
            "name": "Second Tenant Product",
            "sku": "SHARED-001",
            "unit_price": "15.00",
            "tax_rate": "21.00",
        },
    )

    assert response.status_code == 201
    assert response.json()["business_id"] == (
        second_business.id
    )


def test_list_products_returns_only_authenticated_business(
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

    own_product = create_product(
        db_session,
        own_business.id,
        name="Own Product",
    )

    other_product = create_product(
        db_session,
        other_business.id,
        name="Other Product",
    )

    response = client.get(
        "/products",
        headers=headers,
    )

    assert response.status_code == 200

    products = response.json()

    returned_ids = {
        product["id"]
        for product in products
    }

    assert own_product.id in returned_ids
    assert other_product.id not in returned_ids

    assert all(
        product["business_id"] == own_business.id
        for product in products
    )


def test_list_products_without_authentication_returns_401(
    client: TestClient,
):
    response = client.get(
        "/products"
    )

    assert response.status_code == 401


def test_get_own_business_product(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    product = create_product(
        db_session,
        business.id,
    )

    response = client.get(
        f"/products/{product.id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == product.id
    assert response.json()["business_id"] == business.id


def test_get_other_business_product_returns_404(
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

    other_product = create_product(
        db_session,
        other_business.id,
    )

    response = client.get(
        f"/products/{other_product.id}",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource not found"
    }


def test_get_nonexistent_product_returns_404(
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
        "/products/999999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_update_own_business_product(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    product = create_product(
        db_session,
        business.id,
        name="Original Product",
        sku="UPDATE-001",
    )

    response = client.patch(
        f"/products/{product.id}",
        headers=headers,
        json={
            "name": "Updated Product",
            "unit_price": "25.50",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Product"
    assert data["sku"] == "UPDATE-001"

    assert Decimal(
        str(data["unit_price"])
    ) == Decimal("25.50")


def test_update_other_business_product_returns_404(
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

    other_product = create_product(
        db_session,
        other_business.id,
    )

    response = client.patch(
        f"/products/{other_product.id}",
        headers=headers,
        json={
            "name": "Forbidden Update",
        },
    )

    assert response.status_code == 404


def test_update_product_with_duplicate_sku_returns_409(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    first_product = create_product(
        db_session,
        business.id,
        sku="FIRST-001",
    )

    second_product = create_product(
        db_session,
        business.id,
        sku="SECOND-001",
    )

    response = client.patch(
        f"/products/{second_product.id}",
        headers=headers,
        json={
            "sku": first_product.sku,
        },
    )

    assert response.status_code == 409


def test_update_product_can_remove_sku(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    product = create_product(
        db_session,
        business.id,
        sku="REMOVE-001",
    )

    response = client.patch(
        f"/products/{product.id}",
        headers=headers,
        json={
            "sku": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["sku"] is None


def test_update_product_rejects_business_id(
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

    product = create_product(
        db_session,
        own_business.id,
    )

    response = client.patch(
        f"/products/{product.id}",
        headers=headers,
        json={
            "business_id": other_business.id,
        },
    )

    assert response.status_code == 422


def test_update_product_rejects_is_active(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    product = create_product(
        db_session,
        business.id,
    )

    response = client.patch(
        f"/products/{product.id}",
        headers=headers,
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 422