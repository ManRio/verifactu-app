from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.identity import normalize_email
from app.db.session import get_db
from app.domain.auth.email_delivery import (
    EmailDeliveryUnavailable,
    ensure_email_ready,
    send_activation_email,
)
from app.domain.auth.schemas import (
    LoginRequest,
    OperationMessage,
    RegistrationPendingRead,
    RegistrationRequest,
    ResendVerificationRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.domain.auth.service import AuthService
from app.domain.auth.verification import InvalidVerificationToken, VerificationService
from app.domain.business.service import BusinessAlreadyExistsError
from app.domain.user.model import User
from app.domain.user.schemas import UserRead
from app.domain.user.service import (
    InactiveUserError,
    InvalidUserCredentialsError,
    UnverifiedUserError,
    UserAlreadyExistsError,
    UserBusinessInactiveError,
    UserBusinessNotFoundError,
    UserService,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=RegistrationPendingRead,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegistrationRequest,
    db: Session = Depends(get_db),
) -> RegistrationPendingRead:
    service = AuthService(db)

    try:
        return service.register(data)
    except EmailDeliveryUnavailable as exc:
        raise HTTPException(status_code=503, detail="Servicio de correo no disponible; revisa SMTP y solicita reenvío") from exc
    except BusinessAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A business with that tax ID already exists",
        ) from exc
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with that email already exists",
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)

    try:
        return service.login(data)
    except UnverifiedUserError as exc:
        raise HTTPException(status_code=403, detail="Verifica tu correo electrónico antes de acceder") from exc
    except (
        InvalidUserCredentialsError,
        InactiveUserError,
        UserBusinessInactiveError,
        UserBusinessNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc


@router.get(
    "/me",
    response_model=UserRead,
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user

@router.post("/verify-email", response_model=OperationMessage)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> OperationMessage:
    try:
        VerificationService(db).confirm(payload.token, payload.password)
    except InvalidVerificationToken as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OperationMessage(message="Cuenta activada correctamente")


@router.post("/resend-verification", response_model=OperationMessage)
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)) -> OperationMessage:
    # Mensaje genérico: no revelar si un correo existe en la base de datos.
    try:
        ensure_email_ready()
    except EmailDeliveryUnavailable as exc:
        raise HTTPException(status_code=503, detail="El servicio de correo no está configurado") from exc
    user = UserService(db).get_by_email(normalize_email(str(payload.email)))
    if user is not None and not user.email_verified:
        token = VerificationService(db).resend(user)
        if token:
            try:
                send_activation_email(user.email, user.full_name, token, employee=user.must_set_password)
            except EmailDeliveryUnavailable as exc:
                raise HTTPException(status_code=503, detail="No se pudo enviar el correo; inténtalo más tarde") from exc
    return OperationMessage(message="Si existe una cuenta pendiente, recibirás un enlace de activación")
