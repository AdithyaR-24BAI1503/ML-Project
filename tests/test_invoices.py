from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection

client = TestClient(app)

def test_create_and_list_invoices():
    # Insert or fetch client
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO clients (name, phone, email) VALUES (?, ?, ?)",
                     ("Invoice Test Client", "+919999988888", "invoicetest@example.com"))
        conn.commit()
        client_row = conn.execute("SELECT id FROM clients WHERE name=?", ("Invoice Test Client",)).fetchone()
        client_id = client_row["id"]

    # Create invoice
    res = client.post("/api/invoices", json={
        "client_id": client_id,
        "description": "Consulting and Development Services",
        "amount": 7500.0,
        "due_date": "2026-11-01",
        "upi_id": "test.merchant@upi"
    })
    assert res.status_code in (200, 201)
    data = res.json()
    assert "invoice" in data
    invoice_id = data["invoice"]["id"]

    # List invoices
    list_res = client.get("/api/invoices")
    assert list_res.status_code == 200
    invoices = list_res.json()
    assert len(invoices) >= 1

    # PDF invoice download
    pdf_res = client.get(f"/api/invoices/{invoice_id}/pdf")
    assert pdf_res.status_code == 200
    assert "application/pdf" in pdf_res.headers["content-type"]

    # Send invoice via WhatsApp simulation
    send_res = client.post(f"/api/invoices/{invoice_id}/send")
    assert send_res.status_code == 200
    assert send_res.json()["status"] == "SIMULATED_SENT"
