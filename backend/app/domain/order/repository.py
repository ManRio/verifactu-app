from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.order.model import Order, OrderLine


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        order: Order,
        lines: list[OrderLine],
    ) -> Order:
        order.lines = lines

        self.db.add(order)
        self.db.flush()
        self.db.refresh(order)

        return order

    def get_by_id(
        self,
        order_id: int,
    ) -> Order | None:
        statement = (
            select(Order)
            .options(
                selectinload(Order.lines),
            )
            .where(
                Order.id == order_id,
            )
        )

        return self.db.scalar(statement)

    def list_by_business_id(
        self,
        business_id: int,
    ) -> list[Order]:
        statement = (
            select(Order)
            .options(
                selectinload(Order.lines),
            )
            .where(
                Order.business_id == business_id,
            )
            .order_by(Order.id)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def replace_lines(
        self,
        order: Order,
        lines: list[OrderLine],
    ) -> Order:
        order.lines = lines

        self.db.flush()
        self.db.refresh(order)

        return order