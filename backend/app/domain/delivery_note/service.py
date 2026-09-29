from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.delivery_note.model import DeliveryNote, DeliveryNoteLine
from app.domain.delivery_note.repository import DeliveryNoteRepository
from app.domain.delivery_note.schemas import (
    DeliveryNoteCreate,
    DeliveryNoteLineInput,
    DeliveryNoteUpdate,
)
from app.domain.order.model import Order, OrderLine
from app.domain.order.repository import OrderRepository


class DeliveryNoteBusinessNotFoundError(Exception):
    pass


class DeliveryNoteBusinessInactiveError(Exception):
    pass


class DeliveryNoteOrderNotFoundError(Exception):
    pass


class DeliveryNoteOrderTenantError(Exception):
    pass


class DeliveryNoteOrderNotConfirmedError(Exception):
    pass


class DeliveryNoteOrderLineNotFoundError(Exception):
    pass


class DeliveryNoteDuplicatePositionError(Exception):
    pass


class DeliveryNoteDuplicateOrderLineError(Exception):
    pass


class DeliveryNoteQuantityExceedsOrderedError(Exception):
    pass


class DeliveryNoteQuantityExceedsRemainingError(Exception):
    pass


class DeliveryNoteNotEditableError(Exception):
    pass


class DeliveryNoteCannotConfirmError(Exception):
    pass


class DeliveryNoteCannotCancelError(Exception):
    pass


class DeliveryNoteInvalidDeliveryDateError(Exception):
    pass


class DeliveryNoteService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = DeliveryNoteRepository(db)
        self.business_repository = BusinessRepository(db)
        self.order_repository = OrderRepository(db)

    def create_delivery_note(
        self,
        data: DeliveryNoteCreate,
        *,
        commit: bool = True,
    ) -> DeliveryNote:
        business = self.business_repository.get_by_id(
            data.business_id,
        )

        if business is None:
            raise DeliveryNoteBusinessNotFoundError

        if not business.is_active:
            raise DeliveryNoteBusinessInactiveError

        order = self._get_valid_order(
            business_id=data.business_id,
            order_id=data.order_id,
        )

        self._validate_line_inputs(
            data.lines,
        )

        lines = self._build_lines(
            order=order,
            line_inputs=data.lines,
        )

        delivery_note = DeliveryNote(
            business_id=data.business_id,
            order_id=order.id,
            status="DRAFT",
            delivery_date=data.delivery_date,
            notes=data.notes,
        )

        delivery_note = self.repository.create(
            delivery_note,
            lines,
        )

        if commit:
            self.db.commit()
            self.db.refresh(
                delivery_note
            )

        return delivery_note

    def get_by_id(
        self,
        delivery_note_id: int,
    ) -> DeliveryNote | None:
        return self.repository.get_by_id(
            delivery_note_id,
        )

    def list_by_business_id(
        self,
        business_id: int,
    ) -> list[DeliveryNote]:
        return self.repository.list_by_business_id(
            business_id,
        )

    def list_by_order_id(
        self,
        order_id: int,
    ) -> list[DeliveryNote]:
        return self.repository.list_by_order_id(
            order_id,
        )

    def update_delivery_note(
        self,
        delivery_note_id: int,
        data: DeliveryNoteUpdate,
    ) -> DeliveryNote | None:
        delivery_note = self.repository.get_by_id(
            delivery_note_id,
        )

        if delivery_note is None:
            return None

        if delivery_note.status != "DRAFT":
            raise DeliveryNoteNotEditableError

        order = self._get_valid_order(
            business_id=delivery_note.business_id,
            order_id=delivery_note.order_id,
        )

        update_data = data.model_dump(
            exclude_unset=True,
            exclude={"lines"},
        )

        if "delivery_date" in update_data:
            delivery_date = update_data[
                "delivery_date"
            ]

            if delivery_date is None:
                raise DeliveryNoteInvalidDeliveryDateError

            delivery_note.delivery_date = (
                delivery_date
            )

        if "notes" in update_data:
            delivery_note.notes = (
                update_data["notes"]
            )

        if "lines" in data.model_fields_set:
            line_inputs = data.lines

            if line_inputs is None:
                raise DeliveryNoteNotEditableError

            self._validate_line_inputs(
                line_inputs,
            )

            lines = self._build_lines(
                order=order,
                line_inputs=line_inputs,
            )

            self.repository.replace_lines(
                delivery_note,
                lines,
            )

        self.db.commit()
        self.db.refresh(
            delivery_note
        )

        return self.repository.get_by_id(
            delivery_note.id,
        )

    def confirm_delivery_note(
        self,
        delivery_note_id: int,
    ) -> DeliveryNote | None:
        delivery_note = self.repository.get_by_id(
            delivery_note_id,
        )

        if delivery_note is None:
            return None

        if delivery_note.status != "DRAFT":
            raise DeliveryNoteCannotConfirmError

        order = self._get_valid_order(
            business_id=delivery_note.business_id,
            order_id=delivery_note.order_id,
        )

        if not delivery_note.lines:
            raise DeliveryNoteCannotConfirmError

        order_lines_by_id = {
            order_line.id: order_line
            for order_line in order.lines
        }

        for line in delivery_note.lines:
            order_line = order_lines_by_id.get(
                line.order_line_id
            )

            if order_line is None:
                raise DeliveryNoteOrderLineNotFoundError

            confirmed_quantity = (
                self.repository
                .get_confirmed_quantity_for_order_line(
                    order_line.id
                )
            )

            if (
                confirmed_quantity
                + line.quantity
                > order_line.quantity
            ):
                raise DeliveryNoteQuantityExceedsRemainingError

        delivery_note.status = "CONFIRMED"
        delivery_note.confirmed_at = datetime.now(
            UTC
        )

        self.db.commit()
        self.db.refresh(
            delivery_note
        )

        return self.repository.get_by_id(
            delivery_note.id,
        )

    def cancel_delivery_note(
        self,
        delivery_note_id: int,
    ) -> DeliveryNote | None:
        delivery_note = self.repository.get_by_id(
            delivery_note_id,
        )

        if delivery_note is None:
            return None

        if delivery_note.status not in {
            "DRAFT",
            "CONFIRMED",
        }:
            raise DeliveryNoteCannotCancelError

        delivery_note.status = "CANCELLED"

        self.db.commit()
        self.db.refresh(
            delivery_note
        )

        return self.repository.get_by_id(
            delivery_note.id,
        )

    def _get_valid_order(
        self,
        *,
        business_id: int,
        order_id: int,
    ) -> Order:
        order = self.order_repository.get_by_id(
            order_id,
        )

        if order is None:
            raise DeliveryNoteOrderNotFoundError

        if order.business_id != business_id:
            raise DeliveryNoteOrderTenantError

        if order.status != "CONFIRMED":
            raise DeliveryNoteOrderNotConfirmedError

        return order

    def _build_lines(
        self,
        *,
        order: Order,
        line_inputs: list[
            DeliveryNoteLineInput
        ],
    ) -> list[DeliveryNoteLine]:
        order_lines_by_id = {
            order_line.id: order_line
            for order_line in order.lines
        }

        lines: list[DeliveryNoteLine] = []

        for line_input in line_inputs:
            order_line = order_lines_by_id.get(
                line_input.order_line_id
            )

            if order_line is None:
                raise DeliveryNoteOrderLineNotFoundError

            if (
                line_input.quantity
                > order_line.quantity
            ):
                raise DeliveryNoteQuantityExceedsOrderedError

            lines.append(
                self._build_line(
                    order_line=order_line,
                    line_input=line_input,
                )
            )

        return lines

    @staticmethod
    def _build_line(
        *,
        order_line: OrderLine,
        line_input: DeliveryNoteLineInput,
    ) -> DeliveryNoteLine:
        return DeliveryNoteLine(
            order_line_id=order_line.id,
            description=order_line.description,
            quantity=line_input.quantity,
            unit_price=order_line.unit_price,
            tax_rate=order_line.tax_rate,
            position=line_input.position,
        )

    def _validate_line_inputs(
        self,
        lines: list[
            DeliveryNoteLineInput
        ],
    ) -> None:
        positions = [
            line.position
            for line in lines
        ]

        if len(positions) != len(
            set(positions)
        ):
            raise DeliveryNoteDuplicatePositionError

        order_line_ids = [
            line.order_line_id
            for line in lines
        ]

        if len(order_line_ids) != len(
            set(order_line_ids)
        ):
            raise DeliveryNoteDuplicateOrderLineError