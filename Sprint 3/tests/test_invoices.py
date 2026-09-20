from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection

client = TestClient(app)

def test_create_and_list_invoices():
    # Insert a test client into database
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO clients (name, phone, email) VALUES (?, ?, ?)",
                     ("Sprint3 Test Client", "+919999988888", "s3client@test.com"))
        conn.commit()
        client_row = conn.execute("SELECT id FROM clients WHERE name=?", ("Sprint3 Test Client",)).fetchone()
        client_id = client_row["id"]

    # Create invoice
    res = client.post("/api/invoices", json={
        "client_id": client_id,
        "description": "Web design services",
        "amount": 5000.0,
        "due_date": "2026-10-01",
        "upi_id": "test@upi"
    })
    assert res.status_code == 200
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
    assert pdf_res.headers["content-type"] == "application/pdf"

    # Send invoice
    send_res = client.post(f"/api/invoices/{invoice_id}/send")
    assert send_res.status_code == 200
    assert send_res.json()["status"] == "SIMULATED_SENT"
