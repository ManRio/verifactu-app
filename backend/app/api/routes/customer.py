from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.authorization import ensure_same_business
from app.api.dependencies.tenant import get_current_business_id
from app.db.session import get_db
from app.domain.customer.model import Customer
from app.domain.customer.schemas import (
    CustomerApiCreate,
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
)
from app.domain.customer.service import (
    CustomerAlreadyExistsError,
    CustomerService,
)

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    data: CustomerApiCreate,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Customer:
    service = CustomerService(db)

    try:
        return service.create_customer(
            CustomerCreate(
                business_id=current_business_id,
                tax_id=data.tax_id,
                legal_name=data.legal_name,
                trade_name=data.trade_name,
                address=data.address,
                postal_code=data.postal_code,
                city=data.city,
                province=data.province,
                country_code=data.country_code,
                email=data.email,
                phone=data.phone,
            )
        )

    except CustomerAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer with this tax ID already exists",
        )


@router.get(
    "",
    response_model=list[CustomerRead],
)
def list_customers(
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> list[Customer]:
    service = CustomerService(db)

    return service.list_by_business_id(
        current_business_id
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerRead,
)
def get_customer(
    customer_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Customer:
    service = CustomerService(db)

    customer = service.get_by_id(
        customer_id
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=customer.business_id,
    )

    return customer


@router.patch(
    "/{customer_id}",
    response_model=CustomerRead,
)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Customer:
    service = CustomerService(db)

    customer = service.get_by_id(
        customer_id
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=customer.business_id,
    )

    try:
        updated_customer = service.update_customer(
            customer_id,
            data,
        )

    except CustomerAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A customer with this tax ID already exists",
        )

    if updated_customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return updated_customer


@router.patch(
    "/{customer_id}/deactivate",
    response_model=CustomerRead,
)
def deactivate_customer(
    customer_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Customer:
    service = CustomerService(db)

    customer = service.get_by_id(
        customer_id
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=customer.business_id,
    )

    deactivated_customer = service.deactivate_customer(
        customer_id
    )

    if deactivated_customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return deactivated_customer


@router.patch(
    "/{customer_id}/activate",
    response_model=CustomerRead,
)
def activate_customer(
    customer_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Customer:
    service = CustomerService(db)

    customer = service.get_by_id(
        customer_id
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=customer.business_id,
    )

    activated_customer = service.activate_customer(
        customer_id
    )

    if activated_customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return activated_customer