from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.product.model import Product
from app.domain.product.schemas import ProductCreate, ProductUpdate


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        data: ProductCreate,
    ) -> Product:
        product = Product(
            **data.model_dump(),
        )

        self.db.add(product)
        self.db.flush()
        self.db.refresh(product)

        return product

    def get_by_id(
        self,
        product_id: int,
    ) -> Product | None:
        statement = select(Product).where(
            Product.id == product_id,
        )

        return self.db.scalar(statement)

    def get_by_business_id_and_sku(
        self,
        business_id: int,
        sku: str,
    ) -> Product | None:
        statement = select(Product).where(
            Product.business_id == business_id,
            Product.sku == sku,
        )

        return self.db.scalar(statement)

    def list_by_business_id(
        self,
        business_id: int,
    ) -> list[Product]:
        statement = (
            select(Product)
            .where(
                Product.business_id == business_id,
            )
            .order_by(Product.id)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def update(
        self,
        product: Product,
        data: ProductUpdate,
    ) -> Product:
        update_data = data.model_dump(
            exclude_unset=True,
        )

        for field, value in update_data.items():
            setattr(product, field, value)

        self.db.flush()
        self.db.refresh(product)

        return product