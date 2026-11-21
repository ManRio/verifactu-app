"""Cobros de facturas: trazabilidad, seguridad multiempresa y saldos."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import BusinessService
from app.domain.customer.schemas import CustomerCreate
from app.domain.customer.service import CustomerService
from app.domain.delivery_note.schemas import DeliveryNoteCreate, DeliveryNoteLineInput
from app.domain.delivery_note.service import DeliveryNoteService
from app.domain.invoice.schemas import InvoiceCreate, InvoiceIssue
from app.domain.invoice.service import InvoiceService
from app.domain.order.schemas import OrderCreate, OrderLineInput
from app.domain.order.service import OrderService
from app.domain.product.schemas import ProductCreate
from app.domain.product.service import ProductService
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def business_with_token(client: TestClient, db: Session):
    business = BusinessService(db).create_business(BusinessCreate(
        legal_name="Empresa Prueba Cobros SL",
        tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
        address="Calle Prueba 1", postal_code="41001", city="Sevilla",
        province="Sevilla", country_code="ES",
    ))
    email = f"payments-{uuid.uuid4().hex[:12]}@example.com"
    UserService(db).create_user(UserCreate(
        business_id=business.id, email=email, password="password123",
        full_name="Administrador Pruebas",
    ))
    login = client.post("/auth/login", json={"email": email, "password": "password123"})
    assert login.status_code == 200
    return business, {"Authorization": f"Bearer {login.json()['access_token']}"}


def invoice_for_business(db: Session, business_id: int, *, issue: bool = True):
    customer = CustomerService(db).create_customer(CustomerCreate(
        business_id=business_id,
        legal_name="Cliente de pruebas", tax_id=f"CUST-{uuid.uuid4().hex[:12]}",
        trade_name=None, address="Calle Cliente 2", postal_code="41002",
        city="Sevilla", province="Sevilla", country_code="ES",
        email="cliente@example.com", phone=None,
    ))
    product = ProductService(db).create_product(ProductCreate(
        business_id=business_id, name="Producto para cobros",
        sku=f"P-{uuid.uuid4().hex[:12]}", description="Prueba",
        unit_price=Decimal("100.00"), tax_rate=Decimal("21.00"),
    ))
    order_service = OrderService(db)
    order = order_service.create_order(OrderCreate(
        business_id=business_id, customer_id=customer.id, notes=None,
        lines=[OrderLineInput(product_id=product.id, quantity=Decimal("1.000"), position=1)],
    ))
    order_service.confirm_order(order.id)
    note_service = DeliveryNoteService(db)
    note = note_service.create_delivery_note(DeliveryNoteCreate(
        business_id=business_id, order_id=order.id, delivery_date=date(2026, 11, 21),
        notes=None,
        lines=[DeliveryNoteLineInput(order_line_id=order.lines[0].id, quantity=Decimal("1.000"), position=1)],
    ))
    note_service.confirm_delivery_note(note.id)
    invoice_service = InvoiceService(db)
    invoice = invoice_service.create_invoice(InvoiceCreate(
        business_id=business_id, delivery_note_ids=[note.id],
        operation_date=date(2026, 11, 21), notes=None,
    ))
    if issue:
        return invoice_service.issue_invoice(invoice.id, InvoiceIssue(
            series_code="TESTP", issue_date=date(2026, 11, 21),
        ))
    return invoice


@pytest.fixture
def prepared(client: TestClient, db_session: Session):
    business, headers = business_with_token(client, db_session)
    invoice = invoice_for_business(db_session, business.id)
    assert invoice is not None
    assert invoice.total_amount == Decimal("121.00")
    return business, headers, invoice


def payload(invoice_id: int, amount: str = "30.00"):
    return {
        "invoice_id": invoice_id,
        "amount": amount,
        "payment_date": "2026-11-21",
        "method": "TRANSFER",
        "reference": "TEST-TRANSFER-1",
        "notes": "Prueba controlada",
    }


def test_requires_authentication(client: TestClient):
    assert client.get("/payments").status_code == 401
    assert client.get("/payments/invoices/1").status_code == 401
    assert client.post("/payments", json=payload(1)).status_code == 401
    assert client.post("/payments/1/void", json={"reason": "Error"}).status_code == 401


def test_initial_invoice_unpaid(client: TestClient, prepared):
    _, headers, invoice = prepared
    result = client.get("/payments", headers=headers)
    assert result.status_code == 200
    item = next(x for x in result.json() if x["invoice_id"] == invoice.id)
    assert item["payment_status"] == "UNPAID"
    assert Decimal(item["outstanding_amount"]) == Decimal("121.00")


def test_partial_and_complete_payments(client: TestClient, prepared):
    _, headers, invoice = prepared
    first = client.post("/payments", json=payload(invoice.id, "30.00"), headers=headers)
    assert first.status_code == 201, first.text
    assert first.json()["status"] == "RECORDED"
    assert first.json()["created_by_user_id"] > 0
    mid = client.get(f"/payments/invoices/{invoice.id}", headers=headers)
    assert mid.status_code == 200
    assert mid.json()["balance"]["payment_status"] == "PARTIAL"
    assert Decimal(mid.json()["balance"]["outstanding_amount"]) == Decimal("91.00")
    last = client.post("/payments", json=payload(invoice.id, "91.00"), headers=headers)
    assert last.status_code == 201
    final = client.get(f"/payments/invoices/{invoice.id}", headers=headers).json()
    assert final["balance"]["payment_status"] == "PAID"
    assert Decimal(final["balance"]["outstanding_amount"]) == Decimal("0.00")
    assert len(final["payments"]) == 2


def test_overpayment_is_rejected(client: TestClient, prepared):
    _, headers, invoice = prepared
    response = client.post("/payments", json=payload(invoice.id, "121.01"), headers=headers)
    assert response.status_code == 409
    assert "saldo pendiente" in response.json()["detail"]
    ledger = client.get(f"/payments/invoices/{invoice.id}", headers=headers).json()
    assert ledger["payments"] == []


def test_invalid_amount_and_method_rejected(client: TestClient, prepared):
    _, headers, invoice = prepared
    for amount in ("0", "-1", "1.234", "99999999999.99"):
        assert client.post("/payments", json=payload(invoice.id, amount), headers=headers).status_code == 422
    invalid = payload(invoice.id)
    invalid["method"] = "BITCOIN"
    assert client.post("/payments", json=invalid, headers=headers).status_code == 422


def test_void_keeps_audit_and_restores_balance(client: TestClient, prepared):
    _, headers, invoice = prepared
    recorded = client.post("/payments", json=payload(invoice.id), headers=headers).json()
    response = client.post(
        f"/payments/{recorded['id']}/void", json={"reason": "Cobro duplicado"}, headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "VOIDED"
    assert response.json()["void_reason"] == "Cobro duplicado"
    assert response.json()["voided_by_user_id"] > 0
    ledger = client.get(f"/payments/invoices/{invoice.id}", headers=headers).json()
    assert len(ledger["payments"]) == 1
    assert ledger["payments"][0]["status"] == "VOIDED"
    assert ledger["balance"]["payment_status"] == "UNPAID"
    assert client.post(
        f"/payments/{recorded['id']}/void", json={"reason": "Otra vez"}, headers=headers,
    ).status_code == 409


def test_draft_invoice_cannot_receive_payments(client: TestClient, db_session: Session):
    business, headers = business_with_token(client, db_session)
    draft = invoice_for_business(db_session, business.id, issue=False)
    assert client.post("/payments", json=payload(draft.id), headers=headers).status_code == 409
    assert client.get(f"/payments/invoices/{draft.id}", headers=headers).status_code == 409


def test_payments_are_isolated_between_businesses(client: TestClient, db_session: Session, prepared):
    _, first_headers, invoice = prepared
    payment = client.post("/payments", json=payload(invoice.id), headers=first_headers).json()
    _, other_headers = business_with_token(client, db_session)
    assert client.get(f"/payments/invoices/{invoice.id}", headers=other_headers).status_code == 404
    assert client.post("/payments", json=payload(invoice.id), headers=other_headers).status_code == 404
    assert client.post(
        f"/payments/{payment['id']}/void", json={"reason": "No autorizado"}, headers=other_headers,
    ).status_code == 404
    assert not any(x["invoice_id"] == invoice.id for x in client.get("/payments", headers=other_headers).json())


def test_nonexistent_invoice_and_payment_return_404(client: TestClient, db_session: Session):
    _, headers = business_with_token(client, db_session)
    assert client.post("/payments", json=payload(999999999), headers=headers).status_code == 404
    assert client.post("/payments/999999999/void", json={"reason": "Error"}, headers=headers).status_code == 404
