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