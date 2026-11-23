import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.authorization import ensure_same_business
from app.api.dependencies.roles import get_current_superuser
from app.api.dependencies.tenant import get_current_business_id
from app.db.session import get_db
from app.domain.auth.email_delivery import (
    EmailDeliveryUnavailable,
    ensure_email_ready,
    send_activation_email,
)
from app.domain.auth.verification import VerificationService
from app.domain.subscription.quotas import WorkerQuotaError, validate_worker_slots
from app.domain.user.model import User
from app.domain.user.schemas import (
    UserApiCreate,
    UserCreate,
    UserRead,
    UserUpdate,
    WorkerStatusUpdate,
)
from app.domain.user.service import (
    UserAlreadyExistsError,
    UserService,
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: UserApiCreate,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    owner: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> User:
    try:
        ensure_email_ready()
        validate_worker_slots(db, current_business_id)
        user = UserService(db).create_user(
            UserCreate(
                business_id=current_business_id,
                email=data.email,
                password=secrets.token_urlsafe(32),
                full_name=data.full_name,
            ),
            role="WORKER",
            email_verified=False,
            must_set_password=True,
        )
        token = VerificationService(db).issue(user)
        db.commit()
        send_activation_email(user.email, user.full_name, token, employee=True)
        return user
    except WorkerQuotaError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="El correo ya está registrado") from exc
    except EmailDeliveryUnavailable as exc:
        raise HTTPException(status_code=503, detail="No se pudo enviar la invitación; utiliza reenvío") from exc


@router.get(
    "",
    response_model=list[UserRead],
)
def list_users(
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    owner: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> list[User]:
    service = UserService(db)

    return service.list_by_business_id(
        current_business_id
    )


@router.get(
    "/{user_id}",
    response_model=UserRead,
)
def get_user(
    user_id: int,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    owner: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> User:
    service = UserService(db)

    user = service.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=user.business_id,
    )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserRead,
)
def update_user(
    user_id: int,
    data: UserUpdate,
    current_business_id: int = Depends(
        get_current_business_id,
    ),
    owner: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> User:
    service = UserService(db)

    user = service.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    ensure_same_business(
        current_business_id=current_business_id,
        resource_business_id=user.business_id,
    )

    previous_email = user.email

    try:
        updated_user = service.update_user(
            user_id,
            data,
        )

    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if data.email is not None and updated_user.email != previous_email:
        updated_user.email_verified = False
        token = VerificationService(db).issue(updated_user)
        db.commit()
        try:
            send_activation_email(updated_user.email, updated_user.full_name, token, employee=updated_user.must_set_password)
        except EmailDeliveryUnavailable as exc:
            raise HTTPException(status_code=503, detail="Email cambiado; solicita un nuevo enlace de verificación") from exc

    return updated_user

@router.patch("/{user_id}/status", response_model=UserRead)
def set_worker_status(
    user_id: int,
    data: WorkerStatusUpdate,
    current_business_id: int = Depends(get_current_business_id),
    owner: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> User:
    user = UserService(db).get_by_id(user_id)
    if user is None or user.business_id != current_business_id:
        raise HTTPException(status_code=404, detail="Trabajador no encontrado")
    if user.role != "WORKER":
        raise HTTPException(status_code=403, detail="No se puede modificar el superusuario")
    if data.is_active and not user.is_active:
        try:
            validate_worker_slots(db, current_business_id)
        except WorkerQuotaError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
    user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user
