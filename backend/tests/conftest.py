import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.db.session import engine, get_db
from app.main import app

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

