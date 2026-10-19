"""
ChatBiz WhatsApp Reminders Scheduler & Runner
Automates payment reminder notifications (Before Due, Due Today, Overdue).
"""
from datetime import datetime, timedelta
from .database import get_connection

def create_reminder(invoice_id: int, reminder_type: str, scheduled_for: str) -> int:
    """Inserts a new reminder schedule for an invoice."""
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO reminders(invoice_id, reminder_type, scheduled_for) VALUES (?, ?, ?)",
            (invoice_id, reminder_type, scheduled_for)
        )
        conn.commit()
        return cur.lastrowid

def seed_invoice_reminders(invoice_id: int, due_date: str):
    """
    Creates standard 3-tier reminder lifecycle:
    - BEFORE_DUE: 3 days prior
    - DUE_TODAY: on the due date
    - OVERDUE: 1 day past due
    """
    for kind, offset in [("BEFORE_DUE", -3), ("DUE_TODAY", 0), ("OVERDUE", 1)]:
        try:
            # Handles YYYY-MM-DD or full ISO
            clean_date = due_date.split()[0]
            dt = datetime.fromisoformat(clean_date) + timedelta(days=offset)
            scheduled_str = f"{dt.strftime('%Y-%m-%d')} 09:00:00"
            create_reminder(invoice_id, kind, scheduled_str)
        except Exception:
            create_reminder(invoice_id, kind, f"{due_date} 09:00:00")

def run_due_reminders() -> list:
    """
    Identifies all pending reminders scheduled up to the current time,
    marks them as sent (simulated), and returns dispatch telemetry.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT r.*, c.name AS client_name, c.phone AS client_phone, i.description, i.amount
            FROM reminders r
            JOIN invoices i ON r.invoice_id = i.id
            JOIN clients c ON i.client_id = c.id
            WHERE r.status='PENDING' AND r.scheduled_for <= ?
            ORDER BY r.id
        """, (now,)).fetchall()

        results = []
        for r in rows:
            conn.execute(
                "UPDATE reminders SET status='SENT', sent_at=? WHERE id=?",
                (now, r["id"])
            )
            results.append({
                "reminder_id": r["id"],
                "invoice_id": r["invoice_id"],
                "type": r["reminder_type"],
                "client_name": r["client_name"],
                "recipient": r["client_phone"],
                "amount": r["amount"],
                "channel": "WhatsApp Business API (simulated)"
            })
        conn.commit()
        return results
