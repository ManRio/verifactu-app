from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.domain.delivery_note.model import DeliveryNote, DeliveryNoteLine


class DeliveryNoteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        delivery_note: DeliveryNote,
        lines: list[DeliveryNoteLine],
    ) -> DeliveryNote:
        delivery_note.lines = lines

        self.db.add(delivery_note)
        self.db.flush()
        self.db.refresh(delivery_note)

        return delivery_note

    def get_by_id(
        self,
        delivery_note_id: int,
    ) -> DeliveryNote | None:
        statement = (
            select(DeliveryNote)
            .options(
                selectinload(
                    DeliveryNote.lines
                ),
            )
            .where(
                DeliveryNote.id
                == delivery_note_id,
            )
        )

        return self.db.scalar(
            statement
        )

    def list_by_business_id(
        self,
        business_id: int,
    ) -> list[DeliveryNote]:
        statement = (
            select(DeliveryNote)
            .options(
                selectinload(
                    DeliveryNote.lines
                ),
            )
            .where(
                DeliveryNote.business_id
                == business_id,
            )
            .order_by(
                DeliveryNote.id
            )
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )

    def list_by_order_id(
        self,
        order_id: int,
    ) -> list[DeliveryNote]:
        statement = (
            select(DeliveryNote)
            .options(
                selectinload(
                    DeliveryNote.lines
                ),
            )
            .where(
                DeliveryNote.order_id
                == order_id,
            )
            .order_by(
                DeliveryNote.id
            )
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )

    def replace_lines(
        self,
        delivery_note: DeliveryNote,
        lines: list[DeliveryNoteLine],
    ) -> DeliveryNote:
        delivery_note.lines = lines

        self.db.flush()
        self.db.refresh(
            delivery_note
        )

        return delivery_note

    def get_confirmed_quantity_for_order_line(
        self,
        order_line_id: int,
    ) -> Decimal:
        statement = (
            select(
                func.coalesce(
                    func.sum(
                        DeliveryNoteLine.quantity
                    ),
                    Decimal(0),
                )
            )
            .join(
                DeliveryNote,
                DeliveryNote.id
                == DeliveryNoteLine.delivery_note_id,
            )
            .where(
                DeliveryNoteLine.order_line_id
                == order_line_id,
                DeliveryNote.status
                == "CONFIRMED",
            )
        )

        result = self.db.scalar(
            statement
        )

        return Decimal(result or 0)