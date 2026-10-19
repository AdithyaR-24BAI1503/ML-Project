"""
Tests for WhatsApp AI Chat System (Client & Manager sides)
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_history_initialization():
    # Client chat history initializes with welcome message
    res = client.get("/api/chat/history?client_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == "client_1"
    assert len(data["messages"]) >= 1
    assert "Hello" in data["messages"][0]["content"]

    # Manager chat history initializes
    res_mgr = client.get("/api/chat/history?session_id=manager")
    assert res_mgr.status_code == 200
    mgr_data = res_mgr.json()
    assert mgr_data["session_id"] == "manager"
    assert len(mgr_data["messages"]) >= 1


def test_client_chat_balance_inquiry():
    payload = {
        "client_id": 1,
        "message": "What is my outstanding balance and dues?"
    }
    res = client.post("/api/chat/client", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "balance" in data["reply"].lower() or "outstanding" in data["reply"].lower()
    assert data["metadata"]["type"] in ["balance_due", "balance_clear"]


def test_client_chat_invoice_inquiry():
    payload = {
        "client_id": 1,
        "message": "Can I download my latest invoice PDF?"
    }
    res = client.post("/api/chat/client", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "invoice" in data["reply"].lower()
    if data["metadata"]["type"] == "invoice_download":
        assert "download_url" in data["metadata"]


def test_client_chat_payment_info():
    payload = {
        "client_id": 1,
        "message": "How do I pay via UPI or QR code?"
    }
    res = client.post("/api/chat/client", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "chatbiz.merchant@upi" in data["reply"]


def test_client_chat_business_hours():
    payload = {
        "client_id": 1,
        "message": "What are your business hours and office location?"
    }
    res = client.post("/api/chat/client", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "hours" in data["reply"].lower()
    assert "gstin" in data["reply"].lower() or "gst" in data["reply"].lower()


def test_manager_chat_fetch_client_info():
    # Manager requests info for a specific client
    payload = {
        "message": "Show details for client Rajesh Patel"
    }
    res = client.post("/api/chat/manager", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "Rajesh" in data["reply"]
    assert "Financial Ledger" in data["reply"] or "Ledger" in data["reply"]
    assert data["metadata"]["type"] == "client_dossier"


def test_manager_chat_financial_analytics():
    payload = {
        "message": "What is our total revenue and collection rate?"
    }
    res = client.post("/api/chat/manager", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "invoiced" in data["reply"].lower()
    assert "collected" in data["reply"].lower()
    assert data["metadata"]["type"] == "analytics_summary"


def test_manager_chat_create_invoice():
    payload = {
        "message": "Create invoice for Rajesh 3500 due 2026-12-01 for App Design"
    }
    res = client.post("/api/chat/manager", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "invoice" in data["reply"].lower()
    assert data["metadata"]["type"] == "invoice_created"


def test_manager_chat_list_overdue():
    payload = {
        "message": "Show all overdue invoices"
    }
    res = client.post("/api/chat/manager", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "overdue" in data["reply"].lower()


def test_clear_chat():
    res = client.post("/api/chat/clear", json={"session_id": "client_1"})
    assert res.status_code == 200
    assert "Cleared" in res.json()["message"]
