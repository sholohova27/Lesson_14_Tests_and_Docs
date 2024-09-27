import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.db import get_db, Base
from main import app
from src.database.models import Contact
import datetime

@pytest.fixture(scope="module")
def session():
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module", autouse=True)
def setup_database(session):
    initial_contact = Contact(
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        phone_number="1234567890",
        birthday=datetime.date(1990, 1, 1)
    )
    session.add(initial_contact)
    session.commit()
    session.refresh(initial_contact)
    yield initial_contact.id


def test_create_contact(client):
    contact_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "janedoe@example.com",
        "phone_number": "0987654321",
        "birthday": "1991-02-02"
    }
    response = client.post("/contacts/", json=contact_data)
    assert response.status_code == 201
    assert response.json()["first_name"] == contact_data["first_name"]


def test_read_contacts(client):
    response = client.get("/contacts/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_read_contact(client, setup_database):
    response = client.get(f"/contacts/{setup_database}")
    assert response.status_code == 200
    assert response.json()["first_name"] == "John"


def test_update_contact(client, setup_database):
    update_data = {
        "first_name": "John Updated",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "phone_number": "1234567890",
        "birthday": "1990-01-01"
    }
    response = client.put(f"/contacts/{setup_database}", json=update_data)
    assert response.status_code == 200
    assert response.json()["first_name"] == update_data["first_name"]


def test_delete_contact(client, setup_database):
    response = client.delete(f"/contacts/{setup_database}")
    assert response.status_code == 200
    assert response.json()["first_name"] == "John"


def test_search_contacts(client):
    response = client.get("/contacts/search?name=John")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
