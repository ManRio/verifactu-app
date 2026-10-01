from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.invoice.model import (
    Invoice,
    InvoiceDeliveryNote,
    InvoiceLine,
    InvoiceSeries,
)


class InvoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        invoice: Invoice,
        lines: list[InvoiceLine],
        delivery_note_links: list[InvoiceDeliveryNote],
    ) -> Invoice:
        invoice.lines = lines
        invoice.delivery_notes = delivery_note_links

        self.db.add(invoice)
        self.db.flush()
        self.db.refresh(invoice)

        return invoice

    def get_by_id(
        self,
        invoice_id: int,
    ) -> Invoice | None:
        statement = (
            select(Invoice)
            .options(
                selectinload(
                    Invoice.lines,
                ),
                selectinload(
                    Invoice.delivery_notes,
                ),
            )
            .where(
                Invoice.id == invoice_id,
            )
        )

        return self.db.scalar(
            statement
        )

    def list_by_business_id(
        self,
        business_id: int,
    ) -> list[Invoice]:
        statement = (
            select(Invoice)
            .options(
                selectinload(
                    Invoice.lines,
                ),
                selectinload(
                    Invoice.delivery_notes,
                ),
            )
            .where(
                Invoice.business_id
                == business_id,
            )
            .order_by(
                Invoice.id,
            )
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )

    def replace_content(
        self,
        invoice: Invoice,
        lines: list[InvoiceLine],
        delivery_note_links: list[InvoiceDeliveryNote],
    ) -> Invoice:
        invoice.lines = lines
        invoice.delivery_notes = delivery_note_links

        self.db.flush()
        self.db.refresh(
            invoice
        )

        return invoice

    def get_invoice_id_for_delivery_note(
        self,
        delivery_note_id: int,
    ) -> int | None:
        statement = (
            select(
                InvoiceDeliveryNote.invoice_id,
            )
            .where(
                InvoiceDeliveryNote.delivery_note_id
                == delivery_note_id,
            )
        )

        return self.db.scalar(
            statement
        )

    def get_invoiced_delivery_note_ids(
        self,
        delivery_note_ids: list[int],
    ) -> set[int]:
        if not delivery_note_ids:
            return set()

        statement = (
            select(
                InvoiceDeliveryNote.delivery_note_id,
            )
            .where(
                InvoiceDeliveryNote.delivery_note_id.in_(
                    delivery_note_ids
                ),
            )
        )

        return set(
            self.db.scalars(
                statement
            ).all()
        )


class InvoiceSeriesRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        invoice_series: InvoiceSeries,
    ) -> InvoiceSeries:
        self.db.add(
            invoice_series
        )
        self.db.flush()
        self.db.refresh(
            invoice_series
        )

        return invoice_series

    def get_by_business_and_code(
        self,
        business_id: int,
        code: str,
    ) -> InvoiceSeries | None:
        statement = (
            select(InvoiceSeries)
            .where(
                InvoiceSeries.business_id
                == business_id,
                InvoiceSeries.code
                == code,
            )
        )

        return self.db.scalar(
            statement
        )

    def get_by_business_and_code_for_update(
        self,
        business_id: int,
        code: str,
    ) -> InvoiceSeries | None:
        statement = (
            select(InvoiceSeries)
            .where(
                InvoiceSeries.business_id
                == business_id,
                InvoiceSeries.code
                == code,
            )
            .with_for_update()
        )

        return self.db.scalar(
            statement
        )

    def flush(
        self,
        invoice_series: InvoiceSeries,
    ) -> InvoiceSeries:
        self.db.flush()
        self.db.refresh(
            invoice_series
        )

        return invoice_series