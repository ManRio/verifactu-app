from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.business.model import Business
from app.domain.business.schemas import BusinessCreate, BusinessUpdate

class BusinessRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: BusinessCreate) -> Business:
        business = Business(**data.model_dump())

        self.db.add(business)
        self.db.flush()
        self.db.refresh(business)

        return business

    def get_by_id(self, business_id: int) -> Business | None:
        statement = select(Business).where(
            Business.id == business_id
        )

        return self.db.scalar(statement)

    def get_by_tax_id(self, tax_id: str) -> Business | None:
        statement = select(Business).where(
            Business.tax_id == tax_id
        )

        return self.db.scalar(statement)

    def update(
            self,
            business: Business,
            data: BusinessUpdate,
    ) -> Business:
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(business, field, value)

        self.db.flush()
        self.db.refresh(business)

        return business

    def list_all(self) -> list[Business]:
        statement = select(Business).order_by(Business.id)

        return list(self.db.scalars(statement).all())