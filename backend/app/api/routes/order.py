from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.authorization import ensure_same_business
from app.api.dependencies.tenant import get_current_business_id
from app.db.session import get_db
from app.domain.order.model import Order
from app.domain.order.schemas import (
    OrderApiCreate,
    OrderCreate,
    OrderRead,
    OrderUpdate,
)
from app.domain.order.service import (
    OrderBusinessInactiveError,
    OrderBusinessNotFoundError,
    OrderCannotCancelError,
    OrderCannotConfirmError,
    OrderCustomerInactiveError,
    OrderCustomerNotFoundError,
    OrderCustomerTenantError,
    OrderDuplicatePositionError,
    OrderNotEditableError,
    OrderProductInactiveError,
    OrderProductNotFoundError,
    OrderProductTenantError,
    OrderService,
)

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


def raise_order_creation_error(
    error: Exception,
) -> None:
    if isinstance(
        error,
        (
            OrderCustomerNotFoundError,
            OrderCustomerTenantError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    if isinstance(
        error,
        (
            OrderProductNotFoundError,
            OrderProductTenantError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if isinstance(
        error,
        OrderCustomerInactiveError,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer is inactive",
        )

    if isinstance(
        error,
        OrderProductInactiveError,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is inactive",
        )

    if isinstance(
        error,
        OrderDuplicatePositionError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Order line positions must be unique",
        )

    if isinstance(
        error,
        (
            OrderBusinessNotFoundError,
            OrderBusinessInactiveError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid business",
        )

    raise error


@router.post(
    "",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    data: OrderApiCreate,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Order:
    service = OrderService(db)

    try:
        return service.create_order(
            OrderCreate(
                business_id=current_business_id,
                customer_id=data.customer_id,
                notes=data.notes,
                lines=data.lines,
            )
        )

    except (
        OrderBusinessNotFoundError,
        OrderBusinessInactiveError,
        OrderCustomerNotFoundError,
        OrderCustomerInactiveError,
        OrderCustomerTenantError,
        OrderProductNotFoundError,
        OrderProductInactiveError,
        OrderProductTenantError,
        OrderDuplicatePositionError,
    ) as error:
        raise_order_creation_error(error)

    raise RuntimeError(
        "Unexpected order creation state"
    )


@router.get(
    "",
    response_model=list[OrderRead],
)
def list_orders(
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> list[Order]:
    service = OrderService(db)

    return service.list_by_business_id(
        current_business_id
    )


@router.get(
    "/{order_id}",
    response_model=OrderRead,
)
def get_order(
    order_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Order:
    service = OrderService(db)

    order = service.get_by_id(
        order_id
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=order.business_id,
    )

    return order


@router.patch(
    "/{order_id}",
    response_model=OrderRead,
)
def update_order(
    order_id: int,
    data: OrderUpdate,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Order:
    service = OrderService(db)

    order = service.get_by_id(
        order_id
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=order.business_id,
    )

    try:
        updated_order = service.update_order(
            order_id,
            data,
        )

    except OrderNotEditableError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft orders can be edited",
        )

    except (
        OrderCustomerNotFoundError,
        OrderCustomerTenantError,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    except OrderCustomerInactiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer is inactive",
        )

    except (
        OrderProductNotFoundError,
        OrderProductTenantError,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    except OrderProductInactiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is inactive",
        )

    except OrderDuplicatePositionError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Order line positions must be unique",
        )

    if updated_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return updated_order


@router.patch(
    "/{order_id}/confirm",
    response_model=OrderRead,
)
def confirm_order(
    order_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Order:
    service = OrderService(db)

    order = service.get_by_id(
        order_id
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=order.business_id,
    )

    try:
        confirmed_order = service.confirm_order(
            order_id
        )

    except OrderCannotConfirmError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order cannot be confirmed",
        )

    if confirmed_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return confirmed_order


@router.patch(
    "/{order_id}/cancel",
    response_model=OrderRead,
)
def cancel_order(
    order_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Order:
    service = OrderService(db)

    order = service.get_by_id(
        order_id
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=order.business_id,
    )

    try:
        cancelled_order = service.cancel_order(
            order_id
        )

    except OrderCannotCancelError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order cannot be cancelled",
        )

    if cancelled_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return cancelled_order