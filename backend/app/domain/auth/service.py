from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.domain.auth.schemas import (
    LoginRequest,
    RegistrationRequest,
    TokenResponse,
)
from app.domain.business.service import BusinessService
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
        self.business_service = BusinessService(db)

    def login(
        self,
        data: LoginRequest,
    ) -> TokenResponse:
        user = self.user_service.authenticate_user(
            email=str(data.email),
            password=data.password,
        )

        access_token = create_access_token(
            subject=str(user.id)
        )

        return TokenResponse(
            access_token=access_token
        )

    def register(
        self,
        data: RegistrationRequest,
    ) -> TokenResponse:
        try:
            business = self.business_service.create_business(
                data.business,
                commit=False,
            )

            user = self.user_service.create_user(
                UserCreate(
                    business_id=business.id,
                    email=data.user.email,
                    password=data.user.password,
                    full_name=data.user.full_name,
                ),
                commit=False,
            )

            access_token = create_access_token(
                subject=str(user.id)
            )

            self.db.commit()

            return TokenResponse(
                access_token=access_token
            )

        except Exception:
            self.db.rollback()
            raise