import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import BusinessService
from app.domain.customer.schemas import CustomerCreate
from app.domain.customer.service import CustomerService
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def create_business(
    db_session: Session,
):
    service = BusinessService(db_session)

    return service.create_business(
        BusinessCreate(
            legal_name="Customer API Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Cliente 1",
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
                or f"customer-user-{uuid.uuid4().hex[:12]}"
                "@example.com"
            ),
            password="password123",
            full_name="Customer API User",
        )
    )


def get_auth_headers_for_business(
    client: TestClient,
    db_session: Session,
    business_id: int,
) -> dict[str, str]:
    email = (
        f"customer-auth-{uuid.uuid4().hex[:12]}"
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
    legal_name: str = "Test Customer",
    tax_id: str | None = None,
):
    service = CustomerService(db_session)

    return service.create_customer(
        CustomerCreate(
            business_id=business_id,
            tax_id=tax_id,
            legal_name=legal_name,
            trade_name="Customer Trade Name",
            address="Calle Cliente 10",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
            email="customer@example.com",
            phone="600123456",
        )
    )


def test_create_customer_in_authenticated_business(
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
        "/customers",
        headers=headers,
        json={
            "tax_id": "CUSTOMER-001",
            "legal_name": "Customer Example SL",
            "trade_name": "Customer Example",
            "address": "Calle Ejemplo 1",
            "postal_code": "41001",
            "city": "Sevilla",
            "province": "Sevilla",
            "country_code": "ES",
            "email": "example@example.com",
            "phone": "600123456",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["business_id"] == business.id
    assert data["tax_id"] == "CUSTOMER-001"
    assert data["legal_name"] == "Customer Example SL"
    assert data["trade_name"] == "Customer Example"
    assert data["country_code"] == "ES"
    assert data["is_active"] is True


def test_create_customer_does_not_accept_business_id(
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
        "/customers",
        headers=headers,
        json={
            "business_id": other_business.id,
            "tax_id": "CROSS-001",
            "legal_name": "Cross Tenant Customer",
        },
    )

    assert response.status_code == 422


def test_create_customer_without_authentication_returns_401(
    client: TestClient,
):
    response = client.post(
        "/customers",
        json={
            "tax_id": "NOAUTH-001",
            "legal_name": "Unauthenticated Customer",
        },
    )

    assert response.status_code == 401


def test_create_duplicate_tax_id_in_same_business_returns_409(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    create_customer(
        db_session,
        business.id,
        tax_id="DUPLICATE-001",
    )

    response = client.post(
        "/customers",
        headers=headers,
        json={
            "tax_id": "DUPLICATE-001",
            "legal_name": "Duplicate Customer",
        },
    )

    assert response.status_code == 409


def test_same_tax_id_is_allowed_in_different_businesses(
    client: TestClient,
    db_session: Session,
):
    first_business = create_business(db_session)
    second_business = create_business(db_session)

    create_customer(
        db_session,
        first_business.id,
        tax_id="SHARED-001",
    )

    headers = get_auth_headers_for_business(
        client,
        db_session,
        second_business.id,
    )

    response = client.post(
        "/customers",
        headers=headers,
        json={
            "tax_id": "SHARED-001",
            "legal_name": "Second Tenant Customer",
        },
    )

    assert response.status_code == 201
    assert response.json()["business_id"] == (
        second_business.id
    )


def test_multiple_customers_without_tax_id_are_allowed(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    first_response = client.post(
        "/customers",
        headers=headers,
        json={
            "legal_name": "Customer Without Tax ID One",
        },
    )

    second_response = client.post(
        "/customers",
        headers=headers,
        json={
            "legal_name": "Customer Without Tax ID Two",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    assert first_response.json()["tax_id"] is None
    assert second_response.json()["tax_id"] is None


def test_list_customers_returns_only_authenticated_business(
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
        legal_name="Own Customer",
        tax_id="OWN-001",
    )

    other_customer = create_customer(
        db_session,
        other_business.id,
        legal_name="Other Customer",
        tax_id="OTHER-001",
    )

    response = client.get(
        "/customers",
        headers=headers,
    )

    assert response.status_code == 200

    customers = response.json()

    returned_ids = {
        customer["id"]
        for customer in customers
    }

    assert own_customer.id in returned_ids
    assert other_customer.id not in returned_ids

    assert all(
        customer["business_id"] == own_business.id
        for customer in customers
    )


def test_list_customers_without_authentication_returns_401(
    client: TestClient,
):
    response = client.get(
        "/customers"
    )

    assert response.status_code == 401


def test_get_own_business_customer(
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
        tax_id="GET-001",
    )

    response = client.get(
        f"/customers/{customer.id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == customer.id
    assert response.json()["business_id"] == business.id


def test_get_other_business_customer_returns_404(
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

    other_customer = create_customer(
        db_session,
        other_business.id,
        tax_id="OTHER-GET-001",
    )

    response = client.get(
        f"/customers/{other_customer.id}",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource not found"
    }


def test_get_nonexistent_customer_returns_404(
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
        "/customers/999999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_update_own_business_customer(
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
        legal_name="Original Customer",
        tax_id="UPDATE-001",
    )

    response = client.patch(
        f"/customers/{customer.id}",
        headers=headers,
        json={
            "legal_name": "Updated Customer",
            "city": "Dos Hermanas",
            "phone": "611987654",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["legal_name"] == "Updated Customer"
    assert data["tax_id"] == "UPDATE-001"
    assert data["city"] == "Dos Hermanas"
    assert data["phone"] == "611987654"


def test_update_other_business_customer_returns_404(
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

    other_customer = create_customer(
        db_session,
        other_business.id,
        tax_id="OTHER-UPD-001",
    )

    response = client.patch(
        f"/customers/{other_customer.id}",
        headers=headers,
        json={
            "legal_name": "Forbidden Update",
        },
    )

    assert response.status_code == 404


def test_update_customer_with_duplicate_tax_id_returns_409(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    headers = get_auth_headers_for_business(
        client,
        db_session,
        business.id,
    )

    first_customer = create_customer(
        db_session,
        business.id,
        tax_id="FIRST-001",
    )

    second_customer = create_customer(
        db_session,
        business.id,
        tax_id="SECOND-001",
    )

    response = client.patch(
        f"/customers/{second_customer.id}",
        headers=headers,
        json={
            "tax_id": first_customer.tax_id,
        },
    )

    assert response.status_code == 409


def test_update_customer_can_remove_tax_id(
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
        tax_id="REMOVE-001",
    )

    response = client.patch(
        f"/customers/{customer.id}",
        headers=headers,
        json={
            "tax_id": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["tax_id"] is None


def test_update_customer_rejects_business_id(
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
        tax_id="BUSINESS-ID-001",
    )

    response = client.patch(
        f"/customers/{customer.id}",
        headers=headers,
        json={
            "business_id": other_business.id,
        },
    )

    assert response.status_code == 422


def test_update_customer_rejects_is_active(
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
        tax_id="ACTIVE-001",
    )

    response = client.patch(
        f"/customers/{customer.id}",
        headers=headers,
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 422


def test_deactivate_own_business_customer(
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
        tax_id="DEACTIVATE-001",
    )

    response = client.patch(
        f"/customers/{customer.id}/deactivate",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer.id
    assert data["business_id"] == business.id
    assert data["is_active"] is False


def test_activate_own_business_customer(
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
        tax_id="ACTIVATE-001",
    )

    service = CustomerService(db_session)
    service.deactivate_customer(customer.id)

    response = client.patch(
        f"/customers/{customer.id}/activate",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer.id
    assert data["business_id"] == business.id
    assert data["is_active"] is True


def test_deactivate_other_business_customer_returns_404(
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

    other_customer = create_customer(
        db_session,
        other_business.id,
        tax_id="OTHER-DEACT-001",
    )

    response = client.patch(
        f"/customers/{other_customer.id}/deactivate",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource not found"
    }


def test_activate_other_business_customer_returns_404(
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

    other_customer = create_customer(
        db_session,
        other_business.id,
        tax_id="OTHER-ACT-001",
    )

    service = CustomerService(db_session)
    service.deactivate_customer(other_customer.id)

    response = client.patch(
        f"/customers/{other_customer.id}/activate",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource not found"
    }


def test_deactivate_customer_without_authentication_returns_401(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    customer = create_customer(
        db_session,
        business.id,
        tax_id="NOAUTH-DEACT-001",
    )

    response = client.patch(
        f"/customers/{customer.id}/deactivate"
    )

    assert response.status_code == 401


def test_activate_customer_without_authentication_returns_401(
    client: TestClient,
    db_session: Session,
):
    business = create_business(db_session)

    customer = create_customer(
        db_session,
        business.id,
        tax_id="NOAUTH-ACT-001",
    )

    response = client.patch(
        f"/customers/{customer.id}/activate"
    )

    assert response.status_code == 401