"""Verificaciones de generación PDF y controles de acceso básicos."""

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.documents.pdf import Line, Party, PrintableDocument, build_pdf


def demo_data(*, kind="order", status="CONFIRMED") -> PrintableDocument:
    return PrintableDocument(
        kind=kind,
        identifier="TEST-001",
        status=status,
        document_date=date(2026, 11, 21),
        issuer=Party(name="Empresa Demo SL", tax_id="B12345678", city="Sevilla"),
        recipient=Party(name="Cliente Prueba", tax_id="B87654321"),
        lines=(Line(
            description="Artículo de prueba <importante> & detallado",
            quantity=Decimal("2.000"),
            unit_price=Decimal("10.00"),
            tax_rate=Decimal("21.00"),
            total_amount=Decimal("24.20"),
        ),),
        subtotal=Decimal("20.00"),
        tax_total=Decimal("4.20"),
        total_amount=Decimal("24.20"),
        notes="Observaciones\nsegunda línea",
    )


def test_order_pdf_has_valid_signature():
    generated = build_pdf(demo_data())
    assert generated.startswith(b"%PDF-")
    assert len(generated) > 1000


def test_delivery_note_pdf_has_valid_signature():
    generated = build_pdf(demo_data(kind="delivery_note"))
    assert generated.startswith(b"%PDF-")


def test_issued_invoice_pdf_has_valid_signature():
    generated = build_pdf(demo_data(kind="invoice", status="ISSUED"))
    assert generated.startswith(b"%PDF-")


def test_draft_invoice_pdf_is_rejected():
    import pytest

    with pytest.raises(ValueError, match="Solo se pueden imprimir"):
        build_pdf(demo_data(kind="invoice", status="DRAFT"))


def test_pdf_route_requires_authentication(client: TestClient):
    for url in ("/orders/1/pdf", "/delivery-notes/1/pdf", "/invoices/1/pdf"):
        response = client.get(url)
        assert response.status_code in (401, 403)


def test_order_pdf_rejects_document_from_another_business():
    from types import SimpleNamespace
    from unittest.mock import Mock

    import pytest
    from fastapi import HTTPException

    from app.api.routes.documents import order_pdf
    from app.domain.order.model import Order

    order = SimpleNamespace(id=17, business_id=22)
    db = Mock()
    db.get.return_value = order
    with pytest.raises(HTTPException) as exc_info:
        order_pdf(17, current_business_id=21, db=db)
    assert exc_info.value.status_code == 404
    db.get.assert_called_once_with(Order, 17)


def test_invoice_pdf_rejects_draft_before_rendering():
    from types import SimpleNamespace
    from unittest.mock import Mock

    import pytest
    from fastapi import HTTPException

    from app.api.routes.documents import invoice_pdf

    draft = SimpleNamespace(
        id=3, business_id=21, status="DRAFT", issue_date=None,
        full_number=None,
    )
    db = Mock()
    db.get.return_value = draft
    with pytest.raises(HTTPException) as exc_info:
        invoice_pdf(3, current_business_id=21, db=db)
    assert exc_info.value.status_code == 409
