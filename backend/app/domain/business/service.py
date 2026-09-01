from sqlalchemy.orm import Session

from app.domain.business.model import Business
from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate, BusinessUpdate


class BusinessAlreadyExistsError(Exception):
    pass

class BusinessService:
    def __init__(self, db:Session):
        self.db = db
        self.repository = BusinessRepository(db)

    def create_business(self, data: BusinessCreate) -> Business:
        existing_business = self.repository.get_by_tax_id(data.tax_id)

        if existing_business is not None:
            raise BusinessAlreadyExistsError(
                f"A business with tax Id {data.tax_id} already exists"
            )

        business = self.repository.create(data)

        self.db.commit()
        self.db.refresh(business)

        return business

    def get_business(self, business_id: int) -> Business | None:
        return self.repository.get_by_id(business_id)

    def get_business_by_tax_id(self, tax_id: str) -> Business | None:
        return self.repository.get_by_tax_id(tax_id)

    def update_business(
        self,
        business_id: int,
        data: BusinessUpdate,
    ) -> Business | None:
        business = self.repository.get_by_id(business_id)

        if business is None:
            return None

        if data.tax_id is not None and data.tax_id != business.tax_id:
            existing_business = self.repository.get_by_tax_id(data.tax_id)

            if existing_business is not None:
                raise BusinessAlreadyExistsError(
                    f"A business with tax ID {data.tax_id} already exists."
                )

        updated_business = self.repository.update(
            business,
            data,
        )

        self.db.commit()
        self.db.refresh(updated_business)

        return updated_business

    def deactivate_business(
        self,
        business_id: int,
    ) -> Business | None:
        business = self.repository.get_by_id(business_id)

        if business is None:
            return None

        business.is_active = False

        self.db.commit()
        self.db.refresh(business)

        return business

    def activate_business(
        self,
        business_id: int,
    ) -> Business | None:
        business = self.repository.get_by_id(business_id)

        if business is None:
            return None

        business.is_active = True

        self.db.commit()
        self.db.refresh(business)

        return business

    def list_businesses(self) -> list[Business]:
        return self.repository.list_all()