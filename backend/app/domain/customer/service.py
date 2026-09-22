from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.customer.model import Customer
from app.domain.customer.repository import CustomerRepository
from app.domain.customer.schemas import CustomerCreate, CustomerUpdate


class CustomerAlreadyExistsError(Exception):
    pass


class CustomerBusinessNotFoundError(Exception):
    pass


class CustomerBusinessInactiveError(Exception):
    pass


class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CustomerRepository(db)
        self.business_repository = BusinessRepository(db)

    def create_customer(
        self,
        data: CustomerCreate,
        *,
        commit: bool = True,
    ) -> Customer:
        business = self.business_repository.get_by_id(
            data.business_id
        )

        if business is None:
            raise CustomerBusinessNotFoundError

        if not business.is_active:
            raise CustomerBusinessInactiveError

        if data.tax_id is not None:
            existing_customer = (
                self.repository.get_by_business_id_and_tax_id(
                    business_id=data.business_id,
                    tax_id=data.tax_id,
                )
            )

            if existing_customer is not None:
                raise CustomerAlreadyExistsError

        customer = self.repository.create(
            data
        )

        if commit:
            self.db.commit()
            self.db.refresh(customer)

        return customer

    def get_by_id(
        self,
        customer_id: int,
    ) -> Customer | None:
        return self.repository.get_by_id(
            customer_id
        )

    def list_by_business_id(
        self,
        business_id: int,
    ) -> list[Customer]:
        return self.repository.list_by_business_id(
            business_id
        )

    def update_customer(
        self,
        customer_id: int,
        data: CustomerUpdate,
    ) -> Customer | None:
        customer = self.repository.get_by_id(
            customer_id
        )

        if customer is None:
            return None

        update_data = data.model_dump(
            exclude_unset=True,
        )

        if "tax_id" in update_data:
            new_tax_id = update_data["tax_id"]

            if (
                new_tax_id is not None
                and new_tax_id != customer.tax_id
            ):
                existing_customer = (
                    self.repository.get_by_business_id_and_tax_id(
                        business_id=customer.business_id,
                        tax_id=new_tax_id,
                    )
                )

                if (
                    existing_customer is not None
                    and existing_customer.id != customer.id
                ):
                    raise CustomerAlreadyExistsError

        customer = self.repository.update(
            customer,
            data,
        )

        self.db.commit()
        self.db.refresh(customer)

        return customer

    def deactivate_customer(
        self,
        customer_id: int,
    ) -> Customer | None:
        customer = self.repository.get_by_id(
            customer_id
        )

        if customer is None:
            return None

        customer.is_active = False

        self.db.commit()
        self.db.refresh(customer)

        return customer

    def activate_customer(
        self,
        customer_id: int,
    ) -> Customer | None:
        customer = self.repository.get_by_id(
            customer_id
        )

        if customer is None:
            return None

        customer.is_active = True

        self.db.commit()
        self.db.refresh(customer)

        return customer