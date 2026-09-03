from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.domain.auth.schemas import LoginRequest, TokenResponse
from app.domain.user.service import UserService


class AuthService:
    def __init__(self, db: Session):
        self.user_service = UserService(db)

    def login(self, data: LoginRequest) -> TokenResponse:
        user = self.user_service.authenticate_user(
            email=str(data.email),
            password=data.password,
        )

        access_token = create_access_token(
            subject=str(user.id),
        )

        return TokenResponse(
            access_token=access_token,
        )