"""
Basic tests for the Sprint 1 user registration endpoint.
Uses an isolated in-memory SQLite DB so tests never touch chatbiz.db.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_and_teardown():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_register_new_user():
    response = client.post(
        "/users/register",
        json={
            "name": "Rahul Tutor",
            "phone_whatsapp": "+919876543210",
            "business_name": "Rahul's Coaching Classes",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Rahul Tutor"
    assert data["phone_whatsapp"] == "+919876543210"
    assert data["subscription_plan"] == "free"


def test_duplicate_registration_rejected():
    payload = {"name": "Rahul Tutor", "phone_whatsapp": "+919876543210"}
    first = client.post("/users/register", json=payload)
    assert first.status_code == 201

    second = client.post("/users/register", json=payload)
    assert second.status_code == 409


def test_get_user_by_phone():
    client.post(
        "/users/register",
        json={"name": "Priya Kirana", "phone_whatsapp": "+919000011111"},
    )
    response = client.get("/users/+919000011111")
    assert response.status_code == 200
    assert response.json()["name"] == "Priya Kirana"


def test_get_unknown_user_returns_404():
    response = client.get("/users/+910000000000")
    assert response.status_code == 404
