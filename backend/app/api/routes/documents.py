"""Descarga de documentos de demostración en PDF, limitada por empresa."""

import re
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.dependencies.authorization import ensure_same_business
from app.api.dependencies.tenant import get_current_business_id
from app.db.session import get_db
from app.documents.pdf import Line, Party, PrintableDocument, build_pdf
from app.domain.business.model import Business
from app.domain.customer.model import Customer
from app.domain.delivery_note.model import DeliveryNote
from app.domain.invoice.model import Invoice
from app.domain.order.model import Order

router = APIRouter(tags=["documents-demo"])


def _party(source, *, prefix: str = "") -> Party:
    def field(name):
        return getattr(source, f"{prefix}{name}", None)

    return Party(
        name=field("legal_name") or "-",
        tax_id=field("tax_id"),
        address=field("address"),
        postal_code=field("postal_code"),
        city=field("city"),
        province=field("province"),
        country_code=field("country_code"),
    )


def _line(line, *, delivery: bool = False) -> Line:
    return Line(
        description=line.description,
        quantity=Decimal(line.quantity),
        unit_price=None if delivery else Decimal(line.unit_price),
        tax_rate=None if delivery else Decimal(line.tax_rate),
        total_amount=None if delivery else Decimal(line.total_amount),
    )


def _pdf_response(pdf: bytes, filename: str) -> Response:
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)[:100]
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"',
            "Cache-Control": "no-store, private",
            "X-Content-Type-Options": "nosniff",
        },
    )


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")


def _business(db: Session, business_id: int) -> Business:
    business = db.get(Business, business_id)
    if business is None:
        raise _not_found()
    return business


@router.get("/orders/{order_id}/pdf")
def order_pdf(
    order_id: int,
    current_business_id: int = Depends(get_current_business_id),
    db: Session = Depends(get_db),
) -> Response:
    order = db.get(Order, order_id)
    if order is None:
        raise _not_found()
    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=order.business_id,
    )
    business = _business(db, current_business_id)
    customer = db.get(Customer, order.customer_id)
    if customer is None:
        raise _not_found()
    data = PrintableDocument(
        kind="order", identifier=f"#{order.id}", status=order.status,
        document_date=order.created_at,
        issuer=_party(business), recipient=_party(customer),
        lines=tuple(_line(line) for line in order.lines),
        subtotal=order.subtotal, tax_total=order.tax_total,
        total_amount=order.total_amount, notes=order.notes,
    )
    return _pdf_response(build_pdf(data), f"pedido-{order.id}.pdf")


@router.get("/delivery-notes/{delivery_note_id}/pdf")
def delivery_note_pdf(
    delivery_note_id: int,
    current_business_id: int = Depends(get_current_business_id),
    db: Session = Depends(get_db),
) -> Response:
    note = db.get(DeliveryNote, delivery_note_id)
    if note is None:
        raise _not_found()
    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=note.business_id,
    )
    order = note.order
    if order is None or order.business_id != current_business_id:
        raise _not_found()
    business = _business(db, current_business_id)
    customer = db.get(Customer, order.customer_id)
    if customer is None:
        raise _not_found()
    data = PrintableDocument(
        kind="delivery_note", identifier=f"#{note.id}", status=note.status,
        document_date=note.delivery_date,
        issuer=_party(business), recipient=_party(customer),
        lines=tuple(_line(line, delivery=True) for line in note.lines),
        notes=note.notes, references=(f"Pedido de origen: #{order.id}",),
    )
    return _pdf_response(build_pdf(data), f"albaran-{note.id}.pdf")


@router.get("/invoices/{invoice_id}/pdf")
def invoice_pdf(
    invoice_id: int,
    current_business_id: int = Depends(get_current_business_id),
    db: Session = Depends(get_db),
) -> Response:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise _not_found()
    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=invoice.business_id,
    )
    if invoice.status != "ISSUED" or not invoice.issue_date or not invoice.full_number:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Debes emitir la factura antes de descargar su PDF",
        )
    data = PrintableDocument(
        kind="invoice", identifier=invoice.full_number, status=invoice.status,
        document_date=invoice.issue_date,
        issuer=_party(invoice, prefix="issuer_"),
        recipient=_party(invoice, prefix="customer_"),
        lines=tuple(_line(line) for line in invoice.lines),
        subtotal=invoice.subtotal, tax_total=invoice.tax_total,
        total_amount=invoice.total_amount, notes=invoice.notes,
        operation_date=invoice.operation_date,
        references=tuple(
            f"Albarán de origen: #{link.delivery_note_id}"
            for link in invoice.delivery_notes
        ),
    )
    return _pdf_response(build_pdf(data), f"factura-{invoice.full_number}.pdf")
