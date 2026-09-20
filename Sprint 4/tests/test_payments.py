from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection

client = TestClient(app)

def test_record_and_list_payments():
    # Insert client & invoice into database
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO clients (name, phone, email) VALUES (?, ?, ?)",
                     ("Sprint4 Test Client", "+919876500000", "s4client@test.com"))
        conn.commit()
        client_row = conn.execute("SELECT id FROM clients WHERE name=?", ("Sprint4 Test Client",)).fetchone()
        client_id = client_row["id"]

        cur = conn.execute("INSERT INTO invoices (client_id, description, amount, due_date, status) VALUES (?, ?, ?, ?, ?)",
                           (client_id, "Sprint 4 Consulting", 2500.0, "2026-10-15", "Pending"))
        conn.commit()
        invoice_id = cur.lastrowid

    # Record payment
    res = client.post("/api/payments", json={
        "invoice_id": invoice_id,
        "amount": 2500.0,
        "transaction_id": "TXN123456789",
        "payment_date": "2026-09-20"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Paid"
    assert data["total_paid"] == 2500.0

    # List payments
    history_res = client.get("/api/payments")
    assert history_res.status_code == 200
    payments = history_res.json()
    assert len(payments) >= 1
