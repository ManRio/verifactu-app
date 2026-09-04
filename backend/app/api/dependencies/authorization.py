from fastapi import HTTPException, status


def ensure_same_business(
    *,
    current_business_id: int,
    resource_business_id: int,
) -> None:
    if current_business_id != resource_business_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )