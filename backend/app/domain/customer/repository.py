from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.customer.model import Customer
from app.domain.customer.schemas import CustomerCreate, CustomerUpdate


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        data: CustomerCreate,
    ) -> Customer:
        customer = Customer(
            **data.model_dump(),
        )

        self.db.add(customer)
        self.db.flush()
        self.db.refresh(customer)

        return customer

    def get_by_id(
        self,
        customer_id: int,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.id == customer_id,
        )

        return self.db.scalar(statement)

    def get_by_business_id_and_tax_id(
        self,
        business_id: int,
        tax_id: str,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.business_id == business_id,
            Customer.tax_id == tax_id,
        )

        return self.db.scalar(statement)

    def list_by_business_id(
        self,
        business_id: int,
    ) -> list[Customer]:
        statement = (
            select(Customer)
            .where(
                Customer.business_id == business_id,
            )
            .order_by(Customer.id)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def update(
        self,
        customer: Customer,
        data: CustomerUpdate,
    ) -> Customer:
        update_data = data.model_dump(
            exclude_unset=True,
        )

        for field, value in update_data.items():
            setattr(customer, field, value)

        self.db.flush()
        self.db.refresh(customer)

        return customer