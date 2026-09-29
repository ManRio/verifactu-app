from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.authorization import ensure_same_business
from app.api.dependencies.tenant import get_current_business_id
from app.db.session import get_db
from app.domain.delivery_note.model import DeliveryNote
from app.domain.delivery_note.schemas import (
    DeliveryNoteApiCreate,
    DeliveryNoteCreate,
    DeliveryNoteRead,
    DeliveryNoteUpdate,
)
from app.domain.delivery_note.service import (
    DeliveryNoteBusinessInactiveError,
    DeliveryNoteBusinessNotFoundError,
    DeliveryNoteCannotCancelError,
    DeliveryNoteCannotConfirmError,
    DeliveryNoteDuplicateOrderLineError,
    DeliveryNoteDuplicatePositionError,
    DeliveryNoteInvalidDeliveryDateError,
    DeliveryNoteNotEditableError,
    DeliveryNoteOrderLineNotFoundError,
    DeliveryNoteOrderNotConfirmedError,
    DeliveryNoteOrderNotFoundError,
    DeliveryNoteOrderTenantError,
    DeliveryNoteQuantityExceedsOrderedError,
    DeliveryNoteQuantityExceedsRemainingError,
    DeliveryNoteService,
)

router = APIRouter(
    prefix="/delivery-notes",
    tags=["delivery-notes"],
)


def raise_delivery_note_error(
    error: Exception,
) -> None:
    if isinstance(
        error,
        (
            DeliveryNoteOrderNotFoundError,
            DeliveryNoteOrderTenantError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if isinstance(
        error,
        DeliveryNoteOrderNotConfirmedError,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order must be confirmed",
        )

    if isinstance(
        error,
        DeliveryNoteOrderLineNotFoundError,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order line not found",
        )

    if isinstance(
        error,
        DeliveryNoteDuplicatePositionError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Delivery note line positions must be unique",
        )

    if isinstance(
        error,
        DeliveryNoteDuplicateOrderLineError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Order lines cannot be duplicated",
        )

    if isinstance(
        error,
        DeliveryNoteQuantityExceedsOrderedError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Delivery quantity exceeds ordered quantity",
        )

    if isinstance(
        error,
        DeliveryNoteQuantityExceedsRemainingError,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery quantity exceeds remaining quantity",
        )

    if isinstance(
        error,
        DeliveryNoteInvalidDeliveryDateError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid delivery date",
        )

    if isinstance(
        error,
        (
            DeliveryNoteBusinessNotFoundError,
            DeliveryNoteBusinessInactiveError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid business",
        )

    raise error


@router.post(
    "",
    response_model=DeliveryNoteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_delivery_note(
    data: DeliveryNoteApiCreate,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> DeliveryNote:
    service = DeliveryNoteService(db)

    try:
        return service.create_delivery_note(
            DeliveryNoteCreate(
                business_id=current_business_id,
                order_id=data.order_id,
                delivery_date=data.delivery_date,
                notes=data.notes,
                lines=data.lines,
            )
        )

    except (
        DeliveryNoteBusinessNotFoundError,
        DeliveryNoteBusinessInactiveError,
        DeliveryNoteOrderNotFoundError,
        DeliveryNoteOrderTenantError,
        DeliveryNoteOrderNotConfirmedError,
        DeliveryNoteOrderLineNotFoundError,
        DeliveryNoteDuplicatePositionError,
        DeliveryNoteDuplicateOrderLineError,
        DeliveryNoteQuantityExceedsOrderedError,
        DeliveryNoteQuantityExceedsRemainingError,
        DeliveryNoteInvalidDeliveryDateError,
    ) as error:
        raise_delivery_note_error(error)

    raise RuntimeError(
        "Unexpected delivery note creation state"
    )


@router.get(
    "",
    response_model=list[DeliveryNoteRead],
)
def list_delivery_notes(
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> list[DeliveryNote]:
    service = DeliveryNoteService(db)

    return service.list_by_business_id(
        current_business_id
    )


@router.get(
    "/{delivery_note_id}",
    response_model=DeliveryNoteRead,
)
def get_delivery_note(
    delivery_note_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> DeliveryNote:
    service = DeliveryNoteService(db)

    delivery_note = service.get_by_id(
        delivery_note_id
    )

    if delivery_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=delivery_note.business_id,
    )

    return delivery_note


@router.patch(
    "/{delivery_note_id}",
    response_model=DeliveryNoteRead,
)
def update_delivery_note(
    delivery_note_id: int,
    data: DeliveryNoteUpdate,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> DeliveryNote:
    service = DeliveryNoteService(db)

    delivery_note = service.get_by_id(
        delivery_note_id
    )

    if delivery_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=delivery_note.business_id,
    )

    try:
        updated = service.update_delivery_note(
            delivery_note_id,
            data,
        )

    except DeliveryNoteNotEditableError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft delivery notes can be edited",
        )

    except (
        DeliveryNoteOrderNotFoundError,
        DeliveryNoteOrderTenantError,
        DeliveryNoteOrderNotConfirmedError,
        DeliveryNoteOrderLineNotFoundError,
        DeliveryNoteDuplicatePositionError,
        DeliveryNoteDuplicateOrderLineError,
        DeliveryNoteQuantityExceedsOrderedError,
        DeliveryNoteQuantityExceedsRemainingError,
        DeliveryNoteInvalidDeliveryDateError,
    ) as error:
        raise_delivery_note_error(error)

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    return updated


@router.patch(
    "/{delivery_note_id}/confirm",
    response_model=DeliveryNoteRead,
)
def confirm_delivery_note(
    delivery_note_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> DeliveryNote:
    service = DeliveryNoteService(db)

    delivery_note = service.get_by_id(
        delivery_note_id
    )

    if delivery_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=delivery_note.business_id,
    )

    try:
        confirmed = service.confirm_delivery_note(
            delivery_note_id
        )

    except DeliveryNoteCannotConfirmError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery note cannot be confirmed",
        )

    except (
        DeliveryNoteOrderNotFoundError,
        DeliveryNoteOrderTenantError,
        DeliveryNoteOrderNotConfirmedError,
        DeliveryNoteOrderLineNotFoundError,
        DeliveryNoteQuantityExceedsRemainingError,
    ) as error:
        raise_delivery_note_error(error)

    if confirmed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    return confirmed


@router.patch(
    "/{delivery_note_id}/cancel",
    response_model=DeliveryNoteRead,
)
def cancel_delivery_note(
    delivery_note_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> DeliveryNote:
    service = DeliveryNoteService(db)

    delivery_note = service.get_by_id(
        delivery_note_id
    )

    if delivery_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=delivery_note.business_id,
    )

    try:
        cancelled = service.cancel_delivery_note(
            delivery_note_id
        )

    except DeliveryNoteCannotCancelError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery note cannot be cancelled",
        )

    if cancelled is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    return cancelled