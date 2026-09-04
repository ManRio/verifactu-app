from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.domain.auth.schemas import (
    LoginRequest,
    RegistrationRequest,
    TokenResponse,
)
from app.domain.auth.service import AuthService
from app.domain.business.service import BusinessAlreadyExistsError
from app.domain.user.model import User
from app.domain.user.schemas import UserRead
from app.domain.user.service import (
    InactiveUserError,
    InvalidUserCredentialsError,
    UserAlreadyExistsError,
    UserBusinessInactiveError,
    UserBusinessNotFoundError,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegistrationRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)

    try:
        return service.register(data)
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