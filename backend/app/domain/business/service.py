from sqlalchemy.orm import Session

from app.domain.business.model import Business
from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate


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

    