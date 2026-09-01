import uuid

import pytest
from sqlalchemy.orm import Session

from app.domain.business.schemas import BusinessCreate, BusinessUpdate
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
    assert business.is_active is True


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

def test_update_business(db_session):
    service = BusinessService(db_session)

    create_data = BusinessCreate(
        legal_name="Original Service SL",
        tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
        trade_name="Original",
        address="Calle Original 1",
        postal_code="41001",
        city="Sevilla",
        province="Sevilla",
        country_code="ES",
    )

    business = service.create_business(create_data)

    update_data = BusinessUpdate(
        legal_name="Updated Service SL",
        trade_name="Updated",
    )

    updated_business = service.update_business(
        business.id,
        update_data,
    )

    assert updated_business is not None
    assert updated_business.id == business.id
    assert updated_business.legal_name == "Updated Service SL"
    assert updated_business.trade_name == "Updated"

    assert updated_business.tax_id == create_data.tax_id
    assert updated_business.address == "Calle Original 1"


def test_update_nonexistent_business(db_session):
    service = BusinessService(db_session)

    update_data = BusinessUpdate(
        legal_name="Updated Business SL",
    )

    updated_business = service.update_business(
        999999999,
        update_data
    )

    assert updated_business is None

def test_update_business_with_duplicate_tax_id(db_session):
    service = BusinessService(db_session)

    first_business = service.create_business(
        BusinessCreate(
            legal_name="First Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Primera 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    second_business = service.create_business(
        BusinessCreate(
            legal_name="Second Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Segunda 2",
            postal_code="41002",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    update_data = BusinessUpdate(
        tax_id=first_business.tax_id,
    )

    with pytest.raises(BusinessAlreadyExistsError):
        service.update_business(
            second_business.id,
            update_data,
        )

def test_list_businesses(db_session):
    service = BusinessService(db_session)

    first_business = service.create_business(
        BusinessCreate(
            legal_name="First Service List SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Primera 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    second_business = service.create_business(
        BusinessCreate(
            legal_name="Second Service List SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Segunda 2",
            postal_code="41002",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    businesses = service.list_businesses()

    business_ids = [business.id for business in businesses]

    assert first_business.id in business_ids
    assert second_business.id in business_ids
    assert business_ids == sorted(business_ids)

def test_deactivate_business(db_session):
    service = BusinessService(db_session)

    business = service.create_business(
        BusinessCreate(
            legal_name="Deactivate Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Desactivar 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    deactivated_business = service.deactivate_business(
        business.id,
    )

    assert deactivated_business is not None
    assert deactivated_business.id == business.id
    assert deactivated_business.is_active is False

def test_deactivate_nonexistent_business(db_session):
    service = BusinessService(db_session)

    deactivated_business = service.deactivate_business(
        999999999,
    )

    assert deactivated_business is None

def test_activate_business(db_session):
    service = BusinessService(db_session)

    business = service.create_business(
        BusinessCreate(
            legal_name="Activate Business SL",
            tax_id=f"TEST-{uuid.uuid4().hex[:12]}",
            address="Calle Activar 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country_code="ES",
        )
    )

    deactivated_business = service.deactivate_business(
        business.id,
    )

    assert deactivated_business is not None
    assert deactivated_business.is_active is False

    activated_business = service.activate_business(
        business.id,
    )

    assert activated_business is not None
    assert activated_business.id == business.id
    assert activated_business.is_active is True

def test_activate_nonexistent_business(db_session):
    service = BusinessService(db_session)

    activated_business = service.activate_business(
        999999999,
    )

    assert activated_business is None