from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.user.model import User
from app.domain.user.schemas import UserUpdate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        business_id: int,
        email: str,
        password_hash: str,
        full_name: str,
    ) -> User:
        user = User(
            business_id=business_id,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
        )

        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)

        return user

    def get_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self.db.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.scalar(statement)

    def list_by_business_id(
        self,
        business_id: int,
    ) -> list[User]:
        statement = (
            select(User)
            .where(User.business_id == business_id)
            .order_by(User.id)
        )

        return list(self.db.scalars(statement).all())

    def update(
        self,
        user: User,
        data: UserUpdate,
    ) -> User:
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.flush()
        self.db.refresh(user)

        return user