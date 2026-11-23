from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.domain.auth.email_delivery import ensure_email_ready, send_activation_email
from app.domain.auth.schemas import (
    LoginRequest,
    RegistrationPendingRead,
    RegistrationRequest,
    TokenResponse,
)
from app.domain.auth.verification import VerificationService
from app.domain.business.service import BusinessService
from app.domain.subscription.model import Subscription
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
    ) -> RegistrationPendingRead:
        ensure_email_ready()
        try:
            business = self.business_service.create_business(data.business, commit=False)
            user = self.user_service.create_user(
                UserCreate(
                    business_id=business.id,
                    email=data.user.email,
                    password=data.user.password,
                    full_name=data.user.full_name,
                ),
                commit=False,
                role="SUPERUSER",
                email_verified=False,
            )
            token = VerificationService(self.db).issue(user)
            self.db.add(Subscription(business_id=business.id, status="PENDING"))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        # Fuera de la transacción: si SMTP falla, /auth/resend-verification permite reintentar.
        send_activation_email(user.email, user.full_name, token, employee=False)
        return RegistrationPendingRead(message="Revisa tu correo para activar tu cuenta", email=user.email)
