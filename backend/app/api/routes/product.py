from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.authorization import ensure_same_business
from app.api.dependencies.tenant import get_current_business_id
from app.db.session import get_db
from app.domain.product.model import Product
from app.domain.product.schemas import (
    ProductApiCreate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from app.domain.product.service import (
    ProductAlreadyExistsError,
    ProductService,
)

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductApiCreate,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Product:
    service = ProductService(db)

    try:
        return service.create_product(
            ProductCreate(
                business_id=current_business_id,
                name=data.name,
                sku=data.sku,
                description=data.description,
                unit_price=data.unit_price,
                tax_rate=data.tax_rate,
            )
        )

    except ProductAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this SKU already exists",
        )


@router.get(
    "",
    response_model=list[ProductRead],
)
def list_products(
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> list[Product]:
    service = ProductService(db)

    return service.list_by_business_id(
        current_business_id
    )


@router.get(
    "/{product_id}",
    response_model=ProductRead,
)
def get_product(
    product_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Product:
    service = ProductService(db)

    product = service.get_by_id(
        product_id
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=product.business_id,
    )

    return product


@router.patch(
    "/{product_id}",
    response_model=ProductRead,
)
def update_product(
    product_id: int,
    data: ProductUpdate,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Product:
    service = ProductService(db)

    product = service.get_by_id(
        product_id
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=product.business_id,
    )

    try:
        updated_product = service.update_product(
            product_id,
            data,
        )

    except ProductAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this SKU already exists",
        )

    if updated_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return updated_product