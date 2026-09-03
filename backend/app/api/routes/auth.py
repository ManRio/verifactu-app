from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.auth.schemas import LoginRequest, TokenResponse
from app.domain.auth.service import AuthService
from app.domain.user.service import (
    InactiveUserError,
    InvalidUserCredentialsError,
    UserBusinessInactiveError,
    UserBusinessNotFoundError,
)
from app.api.dependencies.auth import get_current_user
from app.domain.user.model import User
from app.domain.user.schemas import UserRead


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


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