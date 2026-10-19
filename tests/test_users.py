import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_register_new_user():
    phone = f"+91987{uuid.uuid4().hex[:7]}"
    response = client.post(
        "/users/register",
        json={
            "name": "Rahul Tutor",
            "phone_whatsapp": phone,
            "business_name": "Rahul's Coaching Classes",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Rahul Tutor"
    assert data["phone_whatsapp"] == phone
    assert data["subscription_plan"] == "free"

def test_duplicate_registration_rejected():
    phone = f"+91988{uuid.uuid4().hex[:7]}"
    payload = {"name": "Test Unique Owner", "phone_whatsapp": phone}
    first = client.post("/users/register", json=payload)
    assert first.status_code == 201

    second = client.post("/users/register", json=payload)
    assert second.status_code == 409

def test_get_user_by_phone():
    phone = f"+91989{uuid.uuid4().hex[:7]}"
    client.post(
        "/users/register",
        json={"name": "Priya Kirana", "phone_whatsapp": phone},
    )
    response = client.get(f"/users/{phone}")
    assert response.status_code == 200
    assert response.json()["name"] == "Priya Kirana"

def test_get_unknown_user_returns_404():
    response = client.get("/users/+910000000000")
    assert response.status_code == 404
