from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.authorization import ensure_same_business
from app.api.dependencies.tenant import get_current_business_id
from app.db.session import get_db
from app.domain.user.model import User
from app.domain.user.schemas import (
    UserApiCreate,
    UserCreate,
    UserRead,
    UserUpdate,
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
    db: Session = Depends(get_db),
) -> User:
    service = UserService(db)

    try:
        return service.create_user(
            UserCreate(
                business_id=current_business_id,
                email=data.email,
                password=data.password,
                full_name=data.full_name,
            )
        )

    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )


@router.get(
    "",
    response_model=list[UserRead],
)
def list_users(
    current_business_id: int = Depends(
        get_current_business_id,
    ),
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

    return updated_user