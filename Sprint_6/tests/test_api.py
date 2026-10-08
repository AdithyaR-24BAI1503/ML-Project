import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "online"
    assert "ChatBiz" in data["app"]
    assert "endpoints" in data

def test_analytics():
    r = client.get("/api/analytics")
    assert r.status_code == 200
    data = r.json()
    assert "overall" in data
    assert "clients" in data
    assert data["overall"]["client_count"] > 0
    assert data["overall"]["invoice_count"] > 0
    assert "collection_rate_pct" in data["overall"]

def test_clients_crud():
    import uuid
    # List clients
    r = client.get("/api/clients")
    assert r.status_code == 200
    clients = r.json()
    assert isinstance(clients, list)
    assert len(clients) >= 8

    # Create client
    new_client_name = f"Test Client {uuid.uuid4().hex[:6]}"
    r2 = client.post("/api/clients", json={
        "name": new_client_name,
        "phone": "+91 99999 11111",
        "email": "test.client@example.com"
    })
    assert r2.status_code == 201
    created_id = r2.json()["client"]["id"]

    # Retrieve single client
    r3 = client.get(f"/api/clients/{created_id}")
    assert r3.status_code == 200
    assert r3.json()["client"]["name"] == new_client_name


def test_invoices_and_status():
    # List all invoices
    r = client.get("/api/invoices")
    assert r.status_code == 200
    invoices = r.json()
    assert len(invoices) >= 16

    # Filter invoices by status
    r_paid = client.get("/api/invoices?status=Paid")
    assert r_paid.status_code == 200
    for inv in r_paid.json():
        assert inv["status"] == "Paid"

    # Create new invoice
    clients = client.get("/api/clients").json()
    first_client_id = clients[0]["id"]
    r_create = client.post("/api/invoices", json={
        "client_id": first_client_id,
        "description": "Test Invoice for Spices Supply",
        "amount": 3200.0,
        "due_date": "2026-10-01",
        "upi_id": "test@upi"
    })
    assert r_create.status_code == 201

    inv_id = r_create.json()["invoice"]["id"]

    # Mark as paid
    r_paid_act = client.post(f"/api/invoices/{inv_id}/mark-paid")
    assert r_paid_act.status_code == 200
    assert r_paid_act.json()["invoice"]["status"] == "Paid"

def test_payments():
    r = client.get("/api/payments")
    assert r.status_code == 200
    payments = r.json()
    assert isinstance(payments, list)
    assert len(payments) >= 7

def test_reminders():
    r = client.get("/api/reminders")
    assert r.status_code == 200
    reminders = r.json()
    assert len(reminders) >= 8

    # Simulate sending first reminder
    rem_id = reminders[0]["id"]
    r_send = client.post(f"/api/reminders/{rem_id}/send")
    assert r_send.status_code == 200
    assert r_send.json()["status"] == "SENT"

def test_voice_commands():
    r = client.get("/api/voice-commands")
    assert r.status_code == 200
    assert len(r.json()) >= 6

    # Log new voice command
    r_new = client.post("/api/voice-commands", json={
        "transcript": "Check pending balance for Ramesh",
        "intent": "VIEW_PENDING"
    })
    assert r_new.status_code == 201
    assert r_new.json()["command"]["transcript"] == "Check pending balance for Ramesh"

def test_export_invoices_csv():
    r = client.get("/api/export/invoices")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "Invoice ID" in r.text
