import uuid

from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate


def test_create_business(db_session: Session):
    repository = BusinessRepository(db_session)

    tax_id = f"TEST-{uuid.uuid4().hex[:12]}"

    data = BusinessCreate(
        legal_name="Empresa Test SL",
        tax_id=tax_id,
        address="Calle Test 1",
        postal_code="41001",
        city="Sevilla",
        province="Sevilla",
    )

    business = repository.create(data)

    assert business.id is not None
    assert business.legal_name == "Empresa Test SL"
    assert business.tax_id == tax_id
    assert business.country_code == "ES"


def test_get_business_by_tax_id(db_session: Session):
    repository = BusinessRepository(db_session)

    tax_id = f"TEST-{uuid.uuid4().hex[:12]}"

    data = BusinessCreate(
        legal_name="Empresa Consulta SL",
        tax_id=tax_id,
        address="Calle Consulta 1",
        postal_code="41002",
        city="Sevilla",
        province="Sevilla",
    )

    created_business = repository.create(data)

    found_business = repository.get_by_tax_id(tax_id)

    assert found_business is not None
    assert found_business.id == created_business.id
    assert found_business.tax_id == tax_id


def test_get_business_by_id(db_session: Session):
    repository = BusinessRepository(db_session)

    tax_id = f"TEST-{uuid.uuid4().hex[:12]}"

    data = BusinessCreate(
        legal_name="Empresa ID SL",
        tax_id=tax_id,
        address="Calle ID 1",
        postal_code="41003",
        city="Sevilla",
        province="Sevilla",
    )

    created_business = repository.create(data)

    found_business = repository.get_by_id(created_business.id)

    assert found_business is not None
    assert found_business.id == created_business.id
    assert found_business.legal_name == "Empresa ID SL"