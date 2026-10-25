"""
Tests for WhatsApp AI Chat System (Client & Manager sides)
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_history_initialization():
    # Ensure fresh initialization
    client.post("/api/chat/clear", json={"session_id": "client_1"})
    client.post("/api/chat/clear", json={"session_id": "manager"})

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


def test_manager_chat_create_invoice_edge_cases():
    # 1. Date before amount should extract the amount, not the year
    res = client.post("/api/chat/manager", json={
        "message": "Create invoice for Rajesh due 2026-11-20 4500 for Website Upgrades"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "invoice_created"
    assert data["metadata"]["amount"] == 4500.0

    # 2. Client ID resolution (e.g. client 2)
    res = client.post("/api/chat/manager", json={
        "message": "Create invoice for client 2 5000 for Consultation"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "invoice_created"
    assert data["metadata"]["client_id"] == 2
    assert data["metadata"]["amount"] == 5000.0

    # 3. Indian numbering format with multiple commas (1,50,000)
    res = client.post("/api/chat/manager", json={
        "message": "Create invoice for Ramesh 1,50,000 for wholesale inventory"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "invoice_created"
    assert data["metadata"]["amount"] == 150000.0

    # 4. Lakh notation
    res = client.post("/api/chat/manager", json={
        "message": "Create invoice for Rajesh 1.5 lakh due 2026-11-30 for fleet services"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "invoice_created"
    assert data["metadata"]["amount"] == 150000.0

    # 5. Currency prefix (Rs 3500)
    res = client.post("/api/chat/manager", json={
        "message": "Create invoice for Rajesh Rs 3500 for App Design"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "invoice_created"
    assert data["metadata"]["amount"] == 3500.0


def test_manager_chat_send_whatsapp_do_the_needy():
    # Manager asks to send whatsapp to a particular client asking them to do the needy
    payload = {
        "message": "Send whatsapp to Rajesh asking them to do the needy"
    }
    res = client.post("/api/chat/manager", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "whatsapp_sent"
    assert "Rajesh" in data["reply"]
    assert "do the needy" in data["metadata"]["message"].lower()

    # Verify that the message is saved in Rajesh's client WhatsApp thread
    client_id = data["metadata"]["client_id"]
    res_hist = client.get(f"/api/chat/history?client_id={client_id}")
    assert res_hist.status_code == 200
    hist = res_hist.json()
    contents = [m["content"] for m in hist["messages"]]
    assert any("do the needy" in c.lower() for c in contents)


def test_manager_chat_send_whatsapp_context_fallback():
    # Manager creates an invoice first
    client.post("/api/chat/manager", json={
        "message": "Create invoice for Priya 2000 for Birthday Cupcakes"
    })
    # Then simply says "send whatsapp asking them to do the needy" without naming client
    res = client.post("/api/chat/manager", json={
        "message": "send whatsapp asking them to do the needy"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "whatsapp_sent"
    assert "Priya" in data["reply"]
    assert "do the needy" in data["metadata"]["message"].lower()


def test_clear_chat():
    res = client.post("/api/chat/clear", json={"session_id": "client_1"})
    assert res.status_code == 200
    assert "Cleared" in res.json()["message"]


def test_manager_chat_create_invoice_screenshot_case():
    # User's exact prompt from screenshot: 'create invoice for sriram 5000 for website optimization'
    # Must properly extract Client: Sriram and Description: Website optimization
    res = client.post("/api/chat/manager", json={
        "message": "create invoice for sriram 5000 for website optimization"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "invoice_created"
    assert data["metadata"]["amount"] == 5000.0
    assert "Sriram" in data["reply"]
    assert "Website optimization" in data["reply"]


def test_manager_chat_create_invoice_no_due_date_case():
    # User's second screenshot: 'create invoice for client john 5000 no due for website optimiztion'
    # Must properly extract Client: John, Description: Website optimization (no 'no due' in desc), Due Date: None
    res = client.post("/api/chat/manager", json={
        "message": "create invoice for client john 5000 no due for website optimiztion"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "invoice_created"
    assert data["metadata"]["amount"] == 5000.0
    assert data["metadata"]["due_date"] is None
    assert "John" in data["reply"]
    assert "Website optimization" in data["reply"]
    assert "No due for" not in data["reply"]
    assert "Due Date:** None" in data["reply"]


def test_client_chat_legitimacy_inquiry():
    # Client asks about the legitimacy of the service provider
    payload = {
        "client_id": 1,
        "message": "Is this service provider legitimate? Please provide official government registries, cross-reference contact and tax records, and show your digital footprint and customer history."
    }
    res = client.post("/api/chat/client", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "legitimacy_verification"
    assert "U72900KA2021PTC148920" in data["reply"]  # MCA CIN
    assert "UDYAM-KR-03-0029418" in data["reply"]     # MSME Udyam
    assert "29AAAAA0000A1Z5" in data["reply"]         # GSTIN
    assert "AAAAA0000A" in data["reply"]              # PAN
    assert "Government Registries" in data["reply"]
    assert "Contact & Tax Records" in data["reply"]
    assert "Digital Footprint" in data["reply"]
    assert "Customer History" in data["reply"]


def test_client_chat_legitimacy_scam_inquiry():
    # Client asks if this is a scam or authentic
    payload = {
        "client_id": 2,
        "message": "Are you legitimate or is this a scam?"
    }
    res = client.post("/api/chat/client", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "legitimacy_verification"
    assert data["metadata"]["verified_badge"] is True
    assert "ChatBiz Solutions" in data["reply"]


def test_client_chat_self_invoice_inquiry():
    # Client asks if they can create an invoice for themselves
    payload = {
        "client_id": 1,
        "message": "can the client able to create a invoice for themselves?"
    }
    res = client.post("/api/chat/client", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "self_invoice_info"
    assert "Yes" in data["reply"]
    assert "create invoice" in data["reply"].lower()


def test_client_chat_create_self_invoice():
    # Client creates an invoice for themselves
    payload = {
        "client_id": 1,
        "message": "create invoice for 4500 for Website Optimization"
    }
    res = client.post("/api/chat/client", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "invoice_created"
    assert data["metadata"]["amount"] == 4500.0
    assert "invoice_id" in data["metadata"]
    assert "download_url" in data["metadata"]
    assert "Website Optimization" in data["reply"]
    assert "4,500" in data["reply"] or "4500" in data["reply"]


def test_client_chat_create_self_invoice_no_due():
    # Client creates an invoice without due date
    payload = {
        "client_id": 2,
        "message": "make invoice 2500 no due for Cloud Migration Services"
    }
    res = client.post("/api/chat/client", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["type"] == "invoice_created"
    assert data["metadata"]["amount"] == 2500.0
    assert data["metadata"]["due_date"] is None
    assert "Due Date:** None" in data["reply"]
    assert "Cloud Migration Services" in data["reply"]


