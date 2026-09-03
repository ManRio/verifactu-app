import uuid

from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.domain.auth.schemas import LoginRequest
from app.domain.auth.service import AuthService
from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate
from app.domain.user.schemas import UserCreate
from app.domain.user.service import UserService


def test_login_returns_access_token(db_session: Session):
    business_repository = BusinessRepository(db_session)
    user_service = UserService(db_session)
    auth_service = AuthService(db_session)

    business = business_repository.create(
        BusinessCreate(
            legal_name="Auth Service Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Login 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    user = user_service.create_user(
        UserCreate(
            business_id=business.id,
            email=f"login-{uuid.uuid4().hex[:12]}@example.com",
            password="password123",
            full_name="Login User",
        )
    )

    response = auth_service.login(
        LoginRequest(
            email=user.email,
            password="password123",
        )
    )

    assert response.token_type == "bearer"
    assert response.access_token

    payload = decode_access_token(
        response.access_token,
    )

    assert payload["sub"] == str(user.id)