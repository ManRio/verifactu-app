from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.authorization import ensure_same_business
from app.api.dependencies.tenant import get_current_business_id
from app.db.session import get_db
from app.domain.business.model import Business
from app.domain.business.schemas import (
    BusinessCreate,
    BusinessRead,
    BusinessUpdate,
)
from app.domain.business.service import BusinessAlreadyExistsError, BusinessService

router = APIRouter(
    prefix= "/businesses",
    tags=["businesses"],
)

@router.post(
    "",
    response_model=BusinessRead,
    status_code=status.HTTP_201_CREATED,
)
def create_business(
    data: BusinessCreate,
    db: Session = Depends(get_db),
):
    service = BusinessService(db)

    try:
        return service.create_business(data)
    except BusinessAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail = str(exc)
        ) from exc

@router.get(
        "",
        response_model=list[BusinessRead],
)
def list_businesses(
    db: Session = Depends(get_db),
):
    service = BusinessService(db)

    return service.list_businesses()

@router.get(
    "/{business_id}",
    response_model=BusinessRead,
)
def get_business(
    business_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Business:
    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=business_id,
    )

    service = BusinessService(db)
    business = service.get_business(business_id)

    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    return business

@router.patch(
    "/{business_id}",
    response_model=BusinessRead,
)
def update_business(
    business_id: int,
    data: BusinessUpdate,
    db: Session = Depends(get_db),
):
    service = BusinessService(db)

    try:
        business = service.update_business(
            business_id,
            data,
        )
    except BusinessAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc)
        ) from exc

    if business is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail="Business not found."
        )

    return business

@router.patch(
    "/{business_id}/deactivate",
    response_model=BusinessRead,
)
def deactivate_business(
    business_id: int,
    db: Session = Depends(get_db),
):
    service = BusinessService(db)

    business = service.deactivate_business(
        business_id,
    )

    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found.",
        )

    return business

@router.patch(
    "/{business_id}/activate",
    response_model=BusinessRead,
)
def activate_business(
    business_id: int,
    db: Session = Depends(get_db),
):
    service = BusinessService(db)

    business = service.activate_business(
        business_id,
    )

    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found.",
        )

    return business