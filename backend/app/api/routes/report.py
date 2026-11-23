"""Panel económico informativo; solo superusuario. No es contabilidad fiscal."""

from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import get_current_superuser
from app.db.session import get_db
from app.domain.invoice.model import Invoice, InvoiceLine
from app.domain.order.model import OrderLine
from app.domain.payment.model import Payment
from app.domain.payment.service import PaymentService
from app.domain.user.model import User

router = APIRouter(prefix="/reports", tags=["reports"])
ZERO = Decimal("0.00")


def _month_bounds(month: str | None) -> tuple[date, date, str]:
    if month is None:
        month = datetime.now(UTC).strftime("%Y-%m")
    if len(month) != 7 or month[4] != "-" or not month[:4].isdigit() or not month[5:].isdigit():
        raise HTTPException(status_code=422, detail="El mes debe tener formato AAAA-MM")
    year, number = int(month[:4]), int(month[5:])
    if not 1 <= year <= 9998 or not 1 <= number <= 12:
        raise HTTPException(status_code=422, detail="Mes no válido")
    start = date(year, number, 1)
    end = date(year + 1, 1, 1) if number == 12 else date(year, number + 1, 1)
    return start, end, month


def _previous_month(start: date) -> date:
    return date(start.year - 1, 12, 1) if start.month == 1 else date(start.year, start.month - 1, 1)


def _money(amount: Decimal) -> str:
    return str(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


@router.get("/summary")
def summary(
    month: str | None = Query(default=None),
    owner: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> dict:
    start, end, selected = _month_bounds(month)
    business_id = owner.business_id

    invoices = list(db.scalars(select(Invoice).where(
        Invoice.business_id == business_id,
        Invoice.status == "ISSUED",
        Invoice.issue_date >= start,
        Invoice.issue_date < end,
    )).all())
    balances = PaymentService(db).list_balances(business_id)
    paid_by_id = {item.invoice_id: Decimal(item.paid_amount) for item in balances}
    outstanding_global = sum((Decimal(row.outstanding_amount) for row in balances), ZERO)
    total_invoiced = sum((Decimal(inv.total_amount) for inv in invoices), ZERO)
    cohort_paid = sum((paid_by_id.get(inv.id, ZERO) for inv in invoices), ZERO)
    pending_cohort = max(total_invoiced - cohort_paid, ZERO)

    cash = db.scalar(select(func.coalesce(func.sum(Payment.amount), ZERO)).where(
        Payment.business_id == business_id,
        Payment.status == "RECORDED",
        Payment.payment_date >= start,
        Payment.payment_date < end,
    ))
    cash_month = Decimal(cash or ZERO)
    ratio = ZERO if total_invoiced <= ZERO else (cohort_paid * 100 / total_invoiced)

    best = db.execute(
        select(
            OrderLine.product_id,
            func.max(InvoiceLine.description).label("description"),
            func.sum(InvoiceLine.quantity).label("units"),
            func.sum(InvoiceLine.total_amount).label("revenue"),
        )
        .select_from(InvoiceLine)
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .join(OrderLine, OrderLine.id == InvoiceLine.order_line_id)
        .where(
            Invoice.business_id == business_id,
            Invoice.status == "ISSUED",
            Invoice.issue_date >= start,
            Invoice.issue_date < end,
        )
        .group_by(OrderLine.product_id)
        .order_by(func.sum(InvoiceLine.quantity).desc(), func.sum(InvoiceLine.total_amount).desc())
        .limit(5)
    ).all()

    months: list[date] = [start]
    for _ in range(5):
        months.insert(0, _previous_month(months[0]))
    first = months[0]
    monthly_invoices = db.execute(select(Invoice.issue_date, Invoice.total_amount).where(
        Invoice.business_id == business_id,
        Invoice.status == "ISSUED",
        Invoice.issue_date >= first,
        Invoice.issue_date < end,
    )).all()
    monthly_payments = db.execute(select(Payment.payment_date, Payment.amount).where(
        Payment.business_id == business_id,
        Payment.status == "RECORDED",
        Payment.payment_date >= first,
        Payment.payment_date < end,
    )).all()

    trend = []
    for beginning in months:
        following = date(beginning.year + 1, 1, 1) if beginning.month == 12 else date(beginning.year, beginning.month + 1, 1)
        billed = sum((Decimal(value) for issued, value in monthly_invoices if beginning <= issued < following), ZERO)
        received = sum((Decimal(value) for day, value in monthly_payments if beginning <= day < following), ZERO)
        trend.append({"month": beginning.strftime("%Y-%m"), "invoiced": _money(billed), "received": _money(received)})

    return {
        "period": selected,
        "issued_invoice_count": len(invoices),
        "total_invoiced": _money(total_invoiced),
        "cash_received_month": _money(cash_month),
        "paid_for_month_invoices": _money(cohort_paid),
        "outstanding_month_invoices": _money(pending_cohort),
        "total_outstanding": _money(outstanding_global),
        "cash_gap": _money(total_invoiced - cash_month),
        "collection_rate": _money(ratio),
        "top_products": [
            {"product_id": product_id, "name": name, "units": str(units), "total_amount": _money(Decimal(revenue))}
            for product_id, name, units, revenue in best
        ],
        "trend": trend,
        "scope": "DEMO",
        "disclaimer": "Datos informativos: los cobros del mes pueden proceder de facturas anteriores. No es contabilidad oficial.",
    }
