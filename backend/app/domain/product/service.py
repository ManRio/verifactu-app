from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.product.model import Product
from app.domain.product.repository import ProductRepository
from app.domain.product.schemas import ProductCreate, ProductUpdate


class ProductAlreadyExistsError(Exception):
    pass


class ProductBusinessNotFoundError(Exception):
    pass


class ProductBusinessInactiveError(Exception):
    pass


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ProductRepository(db)
        self.business_repository = BusinessRepository(db)

    def create_product(
        self,
        data: ProductCreate,
        *,
        commit: bool = True,
    ) -> Product:
        business = self.business_repository.get_by_id(
            data.business_id
        )

        if business is None:
            raise ProductBusinessNotFoundError

        if not business.is_active:
            raise ProductBusinessInactiveError

        if data.sku is not None:
            existing_product = (
                self.repository.get_by_business_id_and_sku(
                    business_id=data.business_id,
                    sku=data.sku,
                )
            )

            if existing_product is not None:
                raise ProductAlreadyExistsError

        product = self.repository.create(
            data
        )

        if commit:
            self.db.commit()
            self.db.refresh(product)

        return product

    def get_by_id(
        self,
        product_id: int,
    ) -> Product | None:
        return self.repository.get_by_id(
            product_id
        )

    def list_by_business_id(
        self,
        business_id: int,
    ) -> list[Product]:
        return self.repository.list_by_business_id(
            business_id
        )

    def update_product(
        self,
        product_id: int,
        data: ProductUpdate,
    ) -> Product | None:
        product = self.repository.get_by_id(
            product_id
        )

        if product is None:
            return None

        update_data = data.model_dump(
            exclude_unset=True,
        )

        if "sku" in update_data:
            new_sku = update_data["sku"]

            if (
                new_sku is not None
                and new_sku != product.sku
            ):
                existing_product = (
                    self.repository.get_by_business_id_and_sku(
                        business_id=product.business_id,
                        sku=new_sku,
                    )
                )

                if (
                    existing_product is not None
                    and existing_product.id != product.id
                ):
                    raise ProductAlreadyExistsError

        product = self.repository.update(
            product,
            data,
        )

        self.db.commit()
        self.db.refresh(product)

        return product

    def deactivate_product(
        self,
        product_id: int,
    ) -> Product | None:
        product = self.repository.get_by_id(
            product_id
        )

        if product is None:
            return None

        product.is_active = False

        self.db.commit()
        self.db.refresh(product)

        return product

    def activate_product(
        self,
        product_id: int,
    ) -> Product | None:
        product = self.repository.get_by_id(
            product_id
        )

        if product is None:
            return None

        product.is_active = True

        self.db.commit()
        self.db.refresh(product)

        return product