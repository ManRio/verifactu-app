from app.api.dependencies.tenant import get_current_business_id
from app.domain.user.model import User


def test_get_current_business_id_returns_user_business_id():
    user = User(
        business_id=42,
        email="tenant@example.com",
        password_hash="hashed-password",
        full_name="Tenant User",
    )

    business_id = get_current_business_id(
        current_user=user,
    )

    assert business_id == 42
