from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.customer.repository import CustomerRepository
from app.domain.delivery_note.model import DeliveryNote
from app.domain.delivery_note.repository import DeliveryNoteRepository
from app.domain.invoice.model import (
    Invoice,
    InvoiceDeliveryNote,
    InvoiceLine,
    InvoiceSeries,
)
from app.domain.invoice.repository import (
    InvoiceRepository,
    InvoiceSeriesRepository,
)
from app.domain.invoice.schemas import (
    InvoiceCreate,
    InvoiceIssue,
    InvoiceUpdate,
)
from app.domain.order.repository import OrderRepository

MONEY_QUANTIZER = Decimal("0.01")
PERCENT_DIVISOR = Decimal(100)


class InvoiceBusinessNotFoundError(Exception):
    pass


class InvoiceBusinessInactiveError(Exception):
    pass


class InvoiceCustomerNotFoundError(Exception):
    pass


class InvoiceDeliveryNoteNotFoundError(Exception):
    pass


class InvoiceDeliveryNoteTenantError(Exception):
    pass


class InvoiceDeliveryNoteNotConfirmedError(Exception):
    pass


class InvoiceDeliveryNoteAlreadyInvoicedError(Exception):
    pass


class InvoiceDuplicateDeliveryNoteError(Exception):
    pass


class InvoiceMixedCustomerError(Exception):
    pass


class InvoiceOrderNotFoundError(Exception):
    pass


class InvoiceNotEditableError(Exception):
    pass


class InvoiceCannotIssueError(Exception):
    pass


class InvoiceInvalidSeriesError(Exception):
    pass


class InvoiceDeliveryNotesRequiredError(Exception):
    pass


class InvoiceService:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.repository = InvoiceRepository(
            db
        )

        self.series_repository = (
            InvoiceSeriesRepository(
                db
            )
        )

        self.business_repository = (
            BusinessRepository(
                db
            )
        )

        self.customer_repository = (
            CustomerRepository(
                db
            )
        )

        self.delivery_note_repository = (
            DeliveryNoteRepository(
                db
            )
        )

        self.order_repository = (
            OrderRepository(
                db
            )
        )

    def create_invoice(
        self,
        data: InvoiceCreate,
        *,
        commit: bool = True,
    ) -> Invoice:
        business = (
            self.business_repository
            .get_by_id(
                data.business_id
            )
        )

        if business is None:
            raise InvoiceBusinessNotFoundError

        if not business.is_active:
            raise InvoiceBusinessInactiveError

        self._validate_delivery_note_ids(
            data.delivery_note_ids
        )

        (
            customer,
            delivery_notes,
        ) = self._get_valid_delivery_notes(
            business_id=data.business_id,
            delivery_note_ids=(
                data.delivery_note_ids
            ),
        )

        lines = self._build_invoice_lines(
            delivery_notes
        )

        (
            subtotal,
            tax_total,
            total_amount,
        ) = self._calculate_invoice_totals(
            lines
        )

        invoice = Invoice(
            business_id=business.id,
            customer_id=customer.id,
            status="DRAFT",
            invoice_type="STANDARD",
            series=None,
            number=None,
            full_number=None,
            issue_date=None,
            operation_date=data.operation_date,
            issuer_legal_name=(
                business.legal_name
            ),
            issuer_tax_id=business.tax_id,
            issuer_address=business.address,
            issuer_postal_code=(
                business.postal_code
            ),
            issuer_city=business.city,
            issuer_province=(
                business.province
            ),
            issuer_country_code=(
                business.country_code
            ),
            customer_legal_name=(
                customer.legal_name
            ),
            customer_tax_id=(
                customer.tax_id
            ),
            customer_address=(
                customer.address
            ),
            customer_postal_code=(
                customer.postal_code
            ),
            customer_city=(
                customer.city
            ),
            customer_province=(
                customer.province
            ),
            customer_country_code=(
                customer.country_code
            ),
            subtotal=subtotal,
            tax_total=tax_total,
            total_amount=total_amount,
            notes=data.notes,
        )

        links = (
            self._build_delivery_note_links(
                delivery_notes
            )
        )

        invoice = self.repository.create(
            invoice,
            lines,
            links,
        )

        if commit:
            self.db.commit()
            self.db.refresh(
                invoice
            )

        return self.repository.get_by_id(
            invoice.id
        )

    def get_by_id(
        self,
        invoice_id: int,
    ) -> Invoice | None:
        return self.repository.get_by_id(
            invoice_id
        )

    def list_by_business_id(
        self,
        business_id: int,
    ) -> list[Invoice]:
        return (
            self.repository
            .list_by_business_id(
                business_id
            )
        )

    def update_invoice(
        self,
        invoice_id: int,
        data: InvoiceUpdate,
    ) -> Invoice | None:
        invoice = self.repository.get_by_id(
            invoice_id
        )

        if invoice is None:
            return None

        if invoice.status != "DRAFT":
            raise InvoiceNotEditableError

        update_data = data.model_dump(
            exclude_unset=True,
            exclude={
                "delivery_note_ids"
            },
        )

        if "operation_date" in update_data:
            invoice.operation_date = (
                update_data[
                    "operation_date"
                ]
            )

        if "notes" in update_data:
            invoice.notes = (
                update_data["notes"]
            )

        if (
            "delivery_note_ids"
            in data.model_fields_set
        ):
            delivery_note_ids = (
                data.delivery_note_ids
            )

            if not delivery_note_ids:
                raise (
                    InvoiceDeliveryNotesRequiredError
                )

            self._validate_delivery_note_ids(
                delivery_note_ids
            )

            (
                customer,
                delivery_notes,
            ) = self._get_valid_delivery_notes(
                business_id=(
                    invoice.business_id
                ),
                delivery_note_ids=(
                    delivery_note_ids
                ),
                current_invoice_id=(
                    invoice.id
                ),
            )

            lines = (
                self._build_invoice_lines(
                    delivery_notes
                )
            )

            (
                subtotal,
                tax_total,
                total_amount,
            ) = (
                self
                ._calculate_invoice_totals(
                    lines
                )
            )

            invoice.customer_id = (
                customer.id
            )

            self._apply_customer_snapshot(
                invoice=invoice,
                customer=customer,
            )

            invoice.subtotal = subtotal
            invoice.tax_total = tax_total
            invoice.total_amount = (
                total_amount
            )

            links = (
                self
                ._build_delivery_note_links(
                    delivery_notes
                )
            )

            self.repository.replace_content(
                invoice,
                lines,
                links,
            )

        self.db.commit()
        self.db.refresh(
            invoice
        )

        return self.repository.get_by_id(
            invoice.id
        )

    def issue_invoice(
        self,
        invoice_id: int,
        data: InvoiceIssue,
    ) -> Invoice | None:
        invoice = self.repository.get_by_id(
            invoice_id
        )

        if invoice is None:
            return None

        if invoice.status != "DRAFT":
            raise InvoiceCannotIssueError

        if (
            not invoice.lines
            or not invoice.delivery_notes
        ):
            raise InvoiceCannotIssueError

        business = (
            self.business_repository
            .get_by_id(
                invoice.business_id
            )
        )

        if business is None:
            raise InvoiceBusinessNotFoundError

        if not business.is_active:
            raise InvoiceBusinessInactiveError

        delivery_note_ids = [
            link.delivery_note_id
            for link in invoice.delivery_notes
        ]

        (
            customer,
            delivery_notes,
        ) = self._get_valid_delivery_notes(
            business_id=(
                invoice.business_id
            ),
            delivery_note_ids=(
                delivery_note_ids
            ),
            current_invoice_id=(
                invoice.id
            ),
        )

        series_code = (
            data.series_code.strip().upper()
        )

        if not series_code:
            raise InvoiceInvalidSeriesError

        series = (
            self._get_or_create_series_for_update(
                business_id=(
                    invoice.business_id
                ),
                code=series_code,
            )
        )

        number = series.next_number

        invoice.invoice_series_id = (
            series.id
        )

        invoice.series = series.code
        invoice.number = number
        invoice.full_number = (
            f"{series.code}-{number:06d}"
        )

        invoice.issue_date = (
            data.issue_date
        )

        invoice.status = "ISSUED"

        invoice.issued_at = datetime.now(
            UTC
        )

        invoice.customer_id = (
            customer.id
        )

        self._apply_issuer_snapshot(
            invoice=invoice,
            business=business,
        )

        self._apply_customer_snapshot(
            invoice=invoice,
            customer=customer,
        )

        lines = self._build_invoice_lines(
            delivery_notes
        )

        (
            subtotal,
            tax_total,
            total_amount,
        ) = self._calculate_invoice_totals(
            lines
        )

        invoice.subtotal = subtotal
        invoice.tax_total = tax_total
        invoice.total_amount = total_amount

        series.next_number = (
            number + 1
        )

        self.series_repository.flush(
            series
        )

        self.db.commit()
        self.db.refresh(
            invoice
        )

        return self.repository.get_by_id(
            invoice.id
        )

    def _get_valid_delivery_notes(
        self,
        *,
        business_id: int,
        delivery_note_ids: list[int],
        current_invoice_id: int | None = None,
    ):
        delivery_notes: list[
            DeliveryNote
        ] = []

        customer = None

        for delivery_note_id in (
            delivery_note_ids
        ):
            delivery_note = (
                self.delivery_note_repository
                .get_by_id(
                    delivery_note_id
                )
            )

            if delivery_note is None:
                raise (
                    InvoiceDeliveryNoteNotFoundError
                )

            if (
                delivery_note.business_id
                != business_id
            ):
                raise (
                    InvoiceDeliveryNoteTenantError
                )

            if (
                delivery_note.status
                != "CONFIRMED"
            ):
                raise (
                    InvoiceDeliveryNoteNotConfirmedError
                )

            existing_invoice_id = (
                self.repository
                .get_invoice_id_for_delivery_note(
                    delivery_note.id
                )
            )

            if (
                existing_invoice_id
                is not None
                and existing_invoice_id
                != current_invoice_id
            ):
                raise (
                    InvoiceDeliveryNoteAlreadyInvoicedError
                )

            order = (
                self.order_repository
                .get_by_id(
                    delivery_note.order_id
                )
            )

            if order is None:
                raise InvoiceOrderNotFoundError

            if (
                order.business_id
                != business_id
            ):
                raise (
                    InvoiceDeliveryNoteTenantError
                )

            order_customer = (
                self.customer_repository
                .get_by_id(
                    order.customer_id
                )
            )

            if order_customer is None:
                raise (
                    InvoiceCustomerNotFoundError
                )

            if (
                order_customer.business_id
                != business_id
            ):
                raise (
                    InvoiceDeliveryNoteTenantError
                )

            if customer is None:
                customer = (
                    order_customer
                )
            elif (
                customer.id
                != order_customer.id
            ):
                raise (
                    InvoiceMixedCustomerError
                )

            delivery_notes.append(
                delivery_note
            )

        if customer is None:
            raise (
                InvoiceDeliveryNotesRequiredError
            )

        return (
            customer,
            delivery_notes,
        )

    def _build_invoice_lines(
        self,
        delivery_notes: list[
            DeliveryNote
        ],
    ) -> list[InvoiceLine]:
        lines: list[
            InvoiceLine
        ] = []

        position = 1

        for delivery_note in (
            delivery_notes
        ):
            for delivery_note_line in (
                delivery_note.lines
            ):
                base_amount = self._money(
                    delivery_note_line.quantity
                    * delivery_note_line.unit_price
                )

                tax_amount = self._money(
                    base_amount
                    * delivery_note_line.tax_rate
                    / PERCENT_DIVISOR
                )

                total_amount = self._money(
                    base_amount
                    + tax_amount
                )

                lines.append(
                    InvoiceLine(
                        delivery_note_line_id=(
                            delivery_note_line.id
                        ),
                        order_line_id=(
                            delivery_note_line.order_line_id
                        ),
                        description=(
                            delivery_note_line.description
                        ),
                        quantity=(
                            delivery_note_line.quantity
                        ),
                        unit_price=(
                            delivery_note_line.unit_price
                        ),
                        tax_rate=(
                            delivery_note_line.tax_rate
                        ),
                        base_amount=(
                            base_amount
                        ),
                        tax_amount=(
                            tax_amount
                        ),
                        total_amount=(
                            total_amount
                        ),
                        position=position,
                    )
                )

                position += 1

        return lines

    @staticmethod
    def _build_delivery_note_links(
        delivery_notes: list[
            DeliveryNote
        ],
    ) -> list[
        InvoiceDeliveryNote
    ]:
        return [
            InvoiceDeliveryNote(
                delivery_note_id=(
                    delivery_note.id
                ),
            )
            for delivery_note
            in delivery_notes
        ]

    def _calculate_invoice_totals(
        self,
        lines: list[
            InvoiceLine
        ],
    ) -> tuple[
        Decimal,
        Decimal,
        Decimal,
    ]:
        subtotal = sum(
            (
                line.base_amount
                for line in lines
            ),
            start=Decimal(0),
        )

        tax_total = sum(
            (
                line.tax_amount
                for line in lines
            ),
            start=Decimal(0),
        )

        total_amount = sum(
            (
                line.total_amount
                for line in lines
            ),
            start=Decimal(0),
        )

        return (
            self._money(
                subtotal
            ),
            self._money(
                tax_total
            ),
            self._money(
                total_amount
            ),
        )

    def _validate_delivery_note_ids(
        self,
        delivery_note_ids: list[int],
    ) -> None:
        if not delivery_note_ids:
            raise (
                InvoiceDeliveryNotesRequiredError
            )

        if (
            len(delivery_note_ids)
            != len(
                set(
                    delivery_note_ids
                )
            )
        ):
            raise (
                InvoiceDuplicateDeliveryNoteError
            )

    def _get_or_create_series_for_update(
        self,
        *,
        business_id: int,
        code: str,
    ) -> InvoiceSeries:
        series = (
            self.series_repository
            .get_by_business_and_code_for_update(
                business_id,
                code,
            )
        )

        if series is not None:
            return series

        try:
            with self.db.begin_nested():
                series = (
                    self.series_repository
                    .create(
                        InvoiceSeries(
                            business_id=(
                                business_id
                            ),
                            code=code,
                            next_number=1,
                        )
                    )
                )

        except IntegrityError:
            series = (
                self.series_repository
                .get_by_business_and_code_for_update(
                    business_id,
                    code,
                )
            )

            if series is None:
                raise

        return series

    @staticmethod
    def _apply_issuer_snapshot(
        *,
        invoice: Invoice,
        business,
    ) -> None:
        invoice.issuer_legal_name = (
            business.legal_name
        )

        invoice.issuer_tax_id = (
            business.tax_id
        )

        invoice.issuer_address = (
            business.address
        )

        invoice.issuer_postal_code = (
            business.postal_code
        )

        invoice.issuer_city = (
            business.city
        )

        invoice.issuer_province = (
            business.province
        )

        invoice.issuer_country_code = (
            business.country_code
        )

    @staticmethod
    def _apply_customer_snapshot(
        *,
        invoice: Invoice,
        customer,
    ) -> None:
        invoice.customer_legal_name = (
            customer.legal_name
        )

        invoice.customer_tax_id = (
            customer.tax_id
        )

        invoice.customer_address = (
            customer.address
        )

        invoice.customer_postal_code = (
            customer.postal_code
        )

        invoice.customer_city = (
            customer.city
        )

        invoice.customer_province = (
            customer.province
        )

        invoice.customer_country_code = (
            customer.country_code
        )

    @staticmethod
    def _money(
        value: Decimal,
    ) -> Decimal:
        return value.quantize(
            MONEY_QUANTIZER,
            rounding=ROUND_HALF_UP,
        )