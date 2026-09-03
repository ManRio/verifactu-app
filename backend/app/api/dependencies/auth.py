from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.domain.business.repository import BusinessRepository
from app.domain.user.model import User
from app.domain.user.repository import UserRepository


bearer_scheme = HTTPBearer(
    auto_error=False,
)


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme,
    ),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise credentials_exception()

    if credentials.scheme.lower() != "bearer":
        raise credentials_exception()

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception()

        user_id = int(subject)
    except (ValueError, TypeError):
        raise credentials_exception()

    user_repository = UserRepository(db)
    user = user_repository.get_by_id(user_id)

    if user is None:
        raise credentials_exception()

    if not user.is_active:
        raise credentials_exception()

    business_repository = BusinessRepository(db)
    business = business_repository.get_by_id(
        user.business_id,
    )

    if business is None:
        raise credentials_exception()

    if not business.is_active:
        raise credentials_exception()

    return user