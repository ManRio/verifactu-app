from sqlalchemy.orm import Session

from app.core.identity import normalize_email
from app.core.security import (
    hash_password,
    verify_dummy_password,
    verify_password,
)
from app.domain.business.repository import BusinessRepository
from app.domain.user.model import User
from app.domain.user.repository import UserRepository
from app.domain.user.schemas import UserCreate, UserUpdate


class UserAlreadyExistsError(Exception):
    pass


class UserBusinessNotFoundError(Exception):
    pass


class UserBusinessInactiveError(Exception):
    pass


class InvalidUserCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)
        self.business_repository = BusinessRepository(db)

    def create_user(
        self,
        data: UserCreate,
    ) -> User:
        business = self.business_repository.get_by_id(
            data.business_id
        )

        if business is None:
            raise UserBusinessNotFoundError

        if not business.is_active:
            raise UserBusinessInactiveError

        normalized_email = normalize_email(
            str(data.email)
        )

        existing_user = self.repository.get_by_email(
            normalized_email
        )

        if existing_user is not None:
            raise UserAlreadyExistsError

        user = self.repository.create(
            business_id=data.business_id,
            email=normalized_email,
            password_hash=hash_password(
                data.password
            ),
            full_name=data.full_name,
        )

        self.db.commit()
        self.db.refresh(user)

        return user

    def get_by_id(
        self,
        user_id: int,
    ) -> User | None:
        return self.repository.get_by_id(
            user_id
        )

    def get_by_email(
        self,
        email: str,
    ) -> User | None:
        return self.repository.get_by_email(
            normalize_email(email)
        )

    def list_by_business_id(
        self,
        business_id: int,
    ) -> list[User]:
        return self.repository.list_by_business_id(
            business_id
        )

    def update_user(
        self,
        user_id: int,
        data: UserUpdate,
    ) -> User | None:
        user = self.repository.get_by_id(
            user_id
        )

        if user is None:
            return None

        if data.email is not None:
            normalized_email = normalize_email(
                str(data.email)
            )

            existing_user = self.repository.get_by_email(
                normalized_email
            )

            if (
                existing_user is not None
                and existing_user.id != user.id
            ):
                raise UserAlreadyExistsError

            data = data.model_copy(
                update={
                    "email": normalized_email,
                }
            )

        user = self.repository.update(
            user,
            data,
        )

        self.db.commit()
        self.db.refresh(user)

        return user

    def deactivate_user(
        self,
        user_id: int,
    ) -> User | None:
        user = self.repository.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.is_active = False

        self.db.commit()
        self.db.refresh(user)

        return user

    def activate_user(
        self,
        user_id: int,
    ) -> User | None:
        user = self.repository.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.is_active = True

        self.db.commit()
        self.db.refresh(user)

        return user

    def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> User:
        normalized_email = normalize_email(
            email
        )

        user = self.repository.get_by_email(
            normalized_email
        )

        if user is None:
            verify_dummy_password(password)
            raise InvalidUserCredentialsError

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise InvalidUserCredentialsError

        if not user.is_active:
            raise InactiveUserError

        business = self.business_repository.get_by_id(
            user.business_id
        )

        if business is None:
            raise UserBusinessNotFoundError

        if not business.is_active:
            raise UserBusinessInactiveError

        return user