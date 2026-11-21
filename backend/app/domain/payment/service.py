"""Conciliación manual de cobros; sin procesamiento real de tarjetas.

No modifica facturas ni crea registros fiscales. Los saldos son derivados de
movimientos RECORDED; la anulación conserva el historial.
"""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.invoice.model import Invoice
from app.domain.payment.model import Payment
from app.domain.payment.schemas import (
    InvoiceBalanceRead,
    InvoicePaymentsRead,
    PaymentCreate,
)

ZERO = Decimal("0.00")


class PaymentInvoiceNotFoundError(Exception):
    pass


class PaymentInvoiceNotIssuedError(Exception):
    pass


class PaymentExceedsOutstandingError(Exception):
    pass


class PaymentNotFoundError(Exception):
    pass


class PaymentAlreadyVoidedError(Exception):
    pass


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    def _invoice(self, business_id: int, invoice_id: int, *, lock: bool = False) -> Invoice:
        stmt = select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.business_id == business_id,
        )
        if lock:
            # Bloquear la factura serializa todos los cobros y anulaciones concurrentes.
            stmt = stmt.with_for_update()
        invoice = self.db.scalar(stmt)
        if invoice is None:
            raise PaymentInvoiceNotFoundError
        return invoice

    def _paid_amount(self, business_id: int, invoice_id: int) -> Decimal:
        result = self.db.scalar(
            select(func.coalesce(func.sum(Payment.amount), ZERO)).where(
                Payment.business_id == business_id,
                Payment.invoice_id == invoice_id,
                Payment.status == "RECORDED",
            )
        )
        return Decimal(result or ZERO)

    @staticmethod
    def _balance(invoice: Invoice, paid_amount: Decimal) -> InvoiceBalanceRead:
        total = Decimal(invoice.total_amount)
        outstanding = total - paid_amount
        outstanding = max(outstanding, ZERO)
        state = "PAID" if outstanding == ZERO else "UNPAID" if paid_amount == ZERO else "PARTIAL"
        return InvoiceBalanceRead(
            invoice_id=invoice.id,
            full_number=invoice.full_number or f"#{invoice.id}",
            customer_legal_name=invoice.customer_legal_name,
            issue_date=invoice.issue_date,
            total_amount=total,
            paid_amount=paid_amount,
            outstanding_amount=outstanding,
            payment_status=state,
        )

    def list_balances(self, business_id: int) -> list[InvoiceBalanceRead]:
        invoices = list(self.db.scalars(
            select(Invoice)
            .where(Invoice.business_id == business_id, Invoice.status == "ISSUED")
            .order_by(Invoice.issue_date.desc(), Invoice.id.desc())
        ).all())
        sums = self.db.execute(
            select(Payment.invoice_id, func.sum(Payment.amount))
            .where(Payment.business_id == business_id, Payment.status == "RECORDED")
            .group_by(Payment.invoice_id)
        ).all()
        paid_by_invoice = {invoice_id: Decimal(amount) for invoice_id, amount in sums}
        return [self._balance(invoice, paid_by_invoice.get(invoice.id, ZERO)) for invoice in invoices]

    def get_invoice_payments(self, business_id: int, invoice_id: int) -> InvoicePaymentsRead:
        invoice = self._invoice(business_id, invoice_id)
        if invoice.status != "ISSUED":
            raise PaymentInvoiceNotIssuedError
        payments = list(self.db.scalars(
            select(Payment)
            .where(Payment.business_id == business_id, Payment.invoice_id == invoice_id)
            .order_by(Payment.created_at.desc(), Payment.id.desc())
        ).all())
        paid = sum((item.amount for item in payments if item.status == "RECORDED"), ZERO)
        return InvoicePaymentsRead(balance=self._balance(invoice, paid), payments=payments)

    def create(self, business_id: int, user_id: int, data: PaymentCreate) -> Payment:
        invoice = self._invoice(business_id, data.invoice_id, lock=True)
        if invoice.status != "ISSUED":
            raise PaymentInvoiceNotIssuedError
        # No usar float para importes. La precisión de 2 decimales ya está
        # validada por Pydantic antes de llegar a este método.
        paid = self._paid_amount(business_id, invoice.id)
        outstanding = Decimal(invoice.total_amount) - paid
        if data.amount > outstanding:
            raise PaymentExceedsOutstandingError
        payment = Payment(
            business_id=business_id,
            invoice_id=invoice.id,
            amount=data.amount,
            payment_date=data.payment_date,
            method=data.method,
            reference=data.reference.strip() or None if data.reference else None,
            notes=data.notes,
            created_by_user_id=user_id,
            status="RECORDED",
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def void(self, business_id: int, user_id: int, payment_id: int, reason: str) -> Payment:
        # Identificación previa sin filtrar datos de otro tenant.
        existing = self.db.scalar(
            select(Payment).where(Payment.id == payment_id, Payment.business_id == business_id)
        )
        if existing is None:
            raise PaymentNotFoundError
        self._invoice(business_id, existing.invoice_id, lock=True)
        # Tanto create como void bloquean la factura en primer lugar.
        payment = self.db.scalar(
            select(Payment).where(Payment.id == payment_id, Payment.business_id == business_id)
            .with_for_update().execution_options(populate_existing=True)
        )
        if payment is None:
            raise PaymentNotFoundError
        if payment.status != "RECORDED":
            raise PaymentAlreadyVoidedError
        payment.status = "VOIDED"
        payment.voided_at = datetime.now(UTC)
        payment.voided_by_user_id = user_id
        payment.void_reason = reason.strip()
        self.db.commit()
        self.db.refresh(payment)
        return payment
