import uuid

from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.business.schemas import BusinessCreate, BusinessUpdate


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


def test_update_business(db_session):
    repository = BusinessRepository(db_session)

    create_data = BusinessCreate(
        legal_name="Original Business SL",
        tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
        trade_name="Original",
        address="Calle Original 1",
        postal_code="41001",
        city="Sevilla",
        province="Sevilla",
        country_code="ES",
    )

    business = repository.create(create_data)

    update_data = BusinessUpdate(
        legal_name="Updated Business SL",
        trade_name="Updated",
    )

    updated_business = repository.update(
        business,
        update_data,
    )

    assert updated_business.id == business.id
    assert updated_business.legal_name == "Updated Business SL"
    assert updated_business.trade_name == "Updated"

    # Los campos no enviados deben conservarse
    assert updated_business.tax_id == create_data.tax_id
    assert updated_business.address == "Calle Original 1"
    assert updated_business.postal_code == "41001"
    assert updated_business.city == "Sevilla"
    assert updated_business.province == "Sevilla"
    assert updated_business.country_code == "ES"