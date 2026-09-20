from datetime import datetime, timedelta
from .database import get_connection

def create_reminder(invoice_id, reminder_type, scheduled_for):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO reminders(invoice_id, reminder_type, scheduled_for) VALUES (?,?,?)",
            (invoice_id, reminder_type, scheduled_for))
        conn.commit()
        return cur.lastrowid

def seed_invoice_reminders(invoice_id, due_date):
    for kind, offset in [("BEFORE_DUE", -3), ("DUE_TODAY", 0), ("OVERDUE", 1)]:
        dt = datetime.fromisoformat(due_date) + timedelta(days=offset)
        create_reminder(invoice_id, kind, dt.isoformat())

def run_due_reminders():
    now = datetime.now().isoformat(timespec="minutes")
    with get_connection() as conn:
        rows = conn.execute('''
            SELECT * FROM reminders
            WHERE status='PENDING' AND scheduled_for <= ?
            ORDER BY id''', (now,)).fetchall()
        results = []
        for r in rows:
            conn.execute(
                "UPDATE reminders SET status='SIMULATED_SENT', sent_at=? WHERE id=?",
                (now, r["id"]))
            results.append({
                "reminder_id": r["id"], "invoice_id": r["invoice_id"],
                "type": r["reminder_type"], "channel": "WhatsApp (mock)"
            })
        conn.commit()
        return results
