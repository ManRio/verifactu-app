from fastapi import Depends

from app.api.dependencies.auth import get_current_user
from app.domain.user.model import User


def get_current_business_id(
    current_user: User = Depends(get_current_user),
) -> int:
    return current_user.business_id