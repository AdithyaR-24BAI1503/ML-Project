from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection

client = TestClient(app)

def test_reminders_and_voice():
    # Seed client and invoice
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO clients (name, phone, email) VALUES (?, ?, ?)",
                     ("Sprint5 Test Client", "+919876511111", "s5client@test.com"))
        conn.commit()
        client_row = conn.execute("SELECT id FROM clients WHERE name=?", ("Sprint5 Test Client",)).fetchone()
        client_id = client_row["id"]

        cur = conn.execute("INSERT INTO invoices (client_id, description, amount, due_date) VALUES (?, ?, ?, ?)",
                           (client_id, "Sprint 5 Tuition", 1500.0, "2026-09-20"))
        conn.commit()
        invoice_id = cur.lastrowid

    # Seed reminders
    seed_res = client.post(f"/api/reminders/seed/{invoice_id}?due_date=2026-09-20")
    assert seed_res.status_code == 200

    # Run reminders
    run_res = client.post("/api/reminders/run")
    assert run_res.status_code == 200
    assert "sent" in run_res.json()

    # List reminders
    list_res = client.get("/api/reminders")
    assert list_res.status_code == 200
    reminders = list_res.json()
    assert len(reminders) >= 1

    # Voice demo
    voice_res = client.post("/api/voice/demo", json={"transcript": "send reminder to sprint5 client"})
    assert voice_res.status_code == 200
    assert voice_res.json()["intent"] is not None

    # Recurring invoice
    rec_res = client.post("/api/recurring-invoices", json={
        "client_id": client_id,
        "description": "Monthly subscription",
        "amount": 1000.0,
        "due_date": "2026-10-01",
        "recurrence": "MONTHLY"
    })
    assert rec_res.status_code == 200
    assert "invoice_id" in rec_res.json()
