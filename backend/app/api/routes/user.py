from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.user.schemas import UserCreate, UserRead, UserUpdate
from app.domain.user.service import (
    UserAlreadyExistsError,
    UserBusinessInactiveError,
    UserBusinessNotFoundError,
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
    data: UserCreate,
    db: Session = Depends(get_db),
):
    service = UserService(db)

    try:
        return service.create_user(data)

    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    except UserBusinessNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    except UserBusinessInactiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Business is inactive",
        )


@router.get(
    "/{user_id}",
    response_model=UserRead,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    user = service.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserRead,
)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
):
    service = UserService(db)

    try:
        user = service.update_user(user_id, data)

    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserRead,
)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    user = service.deactivate_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}/activate",
    response_model=UserRead,
)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    user = service.activate_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user