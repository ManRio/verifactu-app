"""Cobros manuales de facturas; distintos de suscripciones SaaS."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.tenant import get_current_business_id
from app.db.session import get_db
from app.domain.payment.schemas import (
    InvoiceBalanceRead,
    InvoicePaymentsRead,
    PaymentCreate,
    PaymentRead,
    PaymentVoid,
)
from app.domain.payment.service import (
    PaymentAlreadyVoidedError,
    PaymentExceedsOutstandingError,
    PaymentInvoiceNotFoundError,
    PaymentInvoiceNotIssuedError,
    PaymentNotFoundError,
    PaymentService,
)
from app.domain.user.model import User

router = APIRouter(prefix="/payments", tags=["invoice-payments"])


def _raise_payment_error(exc: Exception) -> None:
    if isinstance(exc, (PaymentInvoiceNotFoundError, PaymentNotFoundError)):
        raise HTTPException(status_code=404, detail="Cobro o factura no encontrado") from exc
    if isinstance(exc, PaymentInvoiceNotIssuedError):
        raise HTTPException(status_code=409, detail="Solo se admiten cobros sobre facturas emitidas") from exc
    if isinstance(exc, PaymentExceedsOutstandingError):
        raise HTTPException(status_code=409, detail="El cobro supera el saldo pendiente") from exc
    if isinstance(exc, PaymentAlreadyVoidedError):
        raise HTTPException(status_code=409, detail="Este cobro ya está anulado") from exc
    raise exc


@router.get("", response_model=list[InvoiceBalanceRead])
def list_payment_balances(
    business_id: int = Depends(get_current_business_id),
    db: Session = Depends(get_db),
) -> list[InvoiceBalanceRead]:
    return PaymentService(db).list_balances(business_id)


@router.get("/invoices/{invoice_id}", response_model=InvoicePaymentsRead)
def get_invoice_payments(
    invoice_id: int,
    business_id: int = Depends(get_current_business_id),
    db: Session = Depends(get_db),
) -> InvoicePaymentsRead:
    try:
        return PaymentService(db).get_invoice_payments(business_id, invoice_id)
    except (PaymentInvoiceNotFoundError, PaymentInvoiceNotIssuedError) as exc:
        _raise_payment_error(exc)
    raise RuntimeError("Unexpected payment lookup state")


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def register_payment(
    data: PaymentCreate,
    business_id: int = Depends(get_current_business_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return PaymentService(db).create(business_id, current_user.id, data)
    except (
        PaymentInvoiceNotFoundError,
        PaymentInvoiceNotIssuedError,
        PaymentExceedsOutstandingError,
    ) as exc:
        _raise_payment_error(exc)
    raise RuntimeError("Unexpected payment creation state")


@router.post("/{payment_id}/void", response_model=PaymentRead)
def void_payment(
    payment_id: int,
    data: PaymentVoid,
    business_id: int = Depends(get_current_business_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return PaymentService(db).void(business_id, current_user.id, payment_id, data.reason)
    except (
        PaymentInvoiceNotFoundError,
        PaymentNotFoundError,
        PaymentAlreadyVoidedError,
    ) as exc:
        _raise_payment_error(exc)
    raise RuntimeError("Unexpected payment void state")
