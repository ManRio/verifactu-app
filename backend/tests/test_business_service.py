import uuid

import pytest
from sqlalchemy.orm import Session

from app.domain.business.schemas import BusinessCreate
from app.domain.business.service import (
    BusinessAlreadyExistsError,
    BusinessService,
)


def build_business_data(tax_id: str) -> BusinessCreate:
    return BusinessCreate(
        legal_name="Empresa Service Test SL",
        tax_id=tax_id,
        address="Calle Service 1",
        postal_code="41001",
        city="Sevilla",
        province="Sevilla",
    )


def test_create_business(db_session: Session):
    service = BusinessService(db_session)

    tax_id = f"TEST-{uuid.uuid4().hex[:12]}"
    data = build_business_data(tax_id)

    business = service.create_business(data)

    assert business.id is not None
    assert business.tax_id == tax_id
    assert business.legal_name == "Empresa Service Test SL"


def test_get_business(db_session: Session):
    service = BusinessService(db_session)

    tax_id = f"TEST-{uuid.uuid4().hex[:12]}"
    created_business = service.create_business(
        build_business_data(tax_id)
    )

    found_business = service.get_business(created_business.id)

    assert found_business is not None
    assert found_business.id == created_business.id


def test_duplicate_tax_id_is_rejected(db_session: Session):
    service = BusinessService(db_session)

    tax_id = f"TEST-{uuid.uuid4().hex[:12]}"
    data = build_business_data(tax_id)

    service.create_business(data)

    with pytest.raises(BusinessAlreadyExistsError):
        service.create_business(data)