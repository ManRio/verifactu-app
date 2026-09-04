import pytest
from fastapi import HTTPException

from app.api.dependencies.authorization import ensure_same_business


def test_ensure_same_business_allows_same_business():
    ensure_same_business(
        current_business_id=1,
        resource_business_id=1,
    )


def test_ensure_same_business_rejects_different_business():
    with pytest.raises(HTTPException) as exc_info:
        ensure_same_business(
            current_business_id=1,
            resource_business_id=2,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Resource not found"