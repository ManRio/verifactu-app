from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.authorization import ensure_same_business
from app.api.dependencies.tenant import get_current_business_id
from app.db.session import get_db
from app.domain.invoice.model import Invoice
from app.domain.invoice.schemas import (
    InvoiceApiCreate,
    InvoiceCreate,
    InvoiceIssue,
    InvoiceRead,
    InvoiceUpdate,
)
from app.domain.invoice.service import (
    InvoiceBusinessInactiveError,
    InvoiceBusinessNotFoundError,
    InvoiceCannotIssueError,
    InvoiceCustomerNotFoundError,
    InvoiceDeliveryNoteAlreadyInvoicedError,
    InvoiceDeliveryNoteNotConfirmedError,
    InvoiceDeliveryNoteNotFoundError,
    InvoiceDeliveryNoteTenantError,
    InvoiceDeliveryNotesRequiredError,
    InvoiceDuplicateDeliveryNoteError,
    InvoiceInvalidSeriesError,
    InvoiceMixedCustomerError,
    InvoiceNotEditableError,
    InvoiceOrderNotFoundError,
    InvoiceService,
)


router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
)


def raise_invoice_error(
    error: Exception,
) -> None:
    if isinstance(
        error,
        (
            InvoiceBusinessNotFoundError,
            InvoiceBusinessInactiveError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid business",
        )

    if isinstance(
        error,
        (
            InvoiceDeliveryNoteNotFoundError,
            InvoiceDeliveryNoteTenantError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery note not found",
        )

    if isinstance(
        error,
        InvoiceDeliveryNoteNotConfirmedError,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery note must be confirmed",
        )

    if isinstance(
        error,
        InvoiceDeliveryNoteAlreadyInvoicedError,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery note is already invoiced",
        )

    if isinstance(
        error,
        InvoiceDuplicateDeliveryNoteError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Delivery notes cannot be duplicated",
        )

    if isinstance(
        error,
        InvoiceMixedCustomerError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="All delivery notes must belong to the same customer",
        )

    if isinstance(
        error,
        InvoiceDeliveryNotesRequiredError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="At least one delivery note is required",
        )

    if isinstance(
        error,
        InvoiceOrderNotFoundError,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if isinstance(
        error,
        InvoiceCustomerNotFoundError,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    if isinstance(
        error,
        InvoiceInvalidSeriesError,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid invoice series",
        )

    raise error


@router.post(
    "",
    response_model=InvoiceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_invoice(
    data: InvoiceApiCreate,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Invoice:
    service = InvoiceService(db)

    try:
        return service.create_invoice(
            InvoiceCreate(
                business_id=current_business_id,
                delivery_note_ids=data.delivery_note_ids,
                operation_date=data.operation_date,
                notes=data.notes,
            )
        )

    except (
        InvoiceBusinessNotFoundError,
        InvoiceBusinessInactiveError,
        InvoiceDeliveryNoteNotFoundError,
        InvoiceDeliveryNoteTenantError,
        InvoiceDeliveryNoteNotConfirmedError,
        InvoiceDeliveryNoteAlreadyInvoicedError,
        InvoiceDuplicateDeliveryNoteError,
        InvoiceMixedCustomerError,
        InvoiceDeliveryNotesRequiredError,
        InvoiceOrderNotFoundError,
        InvoiceCustomerNotFoundError,
    ) as error:
        raise_invoice_error(error)

    raise RuntimeError(
        "Unexpected invoice creation state"
    )


@router.get(
    "",
    response_model=list[InvoiceRead],
)
def list_invoices(
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> list[Invoice]:
    service = InvoiceService(db)

    return service.list_by_business_id(
        current_business_id
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceRead,
)
def get_invoice(
    invoice_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Invoice:
    service = InvoiceService(db)

    invoice = service.get_by_id(
        invoice_id
    )

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=invoice.business_id,
    )

    return invoice


@router.patch(
    "/{invoice_id}",
    response_model=InvoiceRead,
)
def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Invoice:
    service = InvoiceService(db)

    invoice = service.get_by_id(
        invoice_id
    )

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=invoice.business_id,
    )

    try:
        updated = service.update_invoice(
            invoice_id,
            data,
        )

    except InvoiceNotEditableError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft invoices can be edited",
        )

    except (
        InvoiceDeliveryNoteNotFoundError,
        InvoiceDeliveryNoteTenantError,
        InvoiceDeliveryNoteNotConfirmedError,
        InvoiceDeliveryNoteAlreadyInvoicedError,
        InvoiceDuplicateDeliveryNoteError,
        InvoiceMixedCustomerError,
        InvoiceDeliveryNotesRequiredError,
        InvoiceOrderNotFoundError,
        InvoiceCustomerNotFoundError,
    ) as error:
        raise_invoice_error(error)

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    return updated


@router.patch(
    "/{invoice_id}/issue",
    response_model=InvoiceRead,
)
def issue_invoice(
    invoice_id: int,
    data: InvoiceIssue,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    db: Session = Depends(get_db),
) -> Invoice:
    service = InvoiceService(db)

    invoice = service.get_by_id(
        invoice_id
    )

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=invoice.business_id,
    )

    try:
        issued = service.issue_invoice(
            invoice_id,
            data,
        )

    except InvoiceCannotIssueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invoice cannot be issued",
        )

    except (
        InvoiceBusinessNotFoundError,
        InvoiceBusinessInactiveError,
        InvoiceDeliveryNoteNotFoundError,
        InvoiceDeliveryNoteTenantError,
        InvoiceDeliveryNoteNotConfirmedError,
        InvoiceDeliveryNoteAlreadyInvoicedError,
        InvoiceMixedCustomerError,
        InvoiceDeliveryNotesRequiredError,
        InvoiceOrderNotFoundError,
        InvoiceCustomerNotFoundError,
        InvoiceInvalidSeriesError,
    ) as error:
        raise_invoice_error(error)

    if issued is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    return issued