"""
Payment Recording & Settlement Business Service
"""
from datetime import date
from ..database import get_connection

def list_invoices():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("""
            SELECT i.*, c.name AS client_name
            FROM invoices i JOIN clients c ON c.id=i.client_id
            ORDER BY i.id DESC
        """).fetchall()]

def record_payment(invoice_id: int, amount: float, transaction_id: str = None, payment_date: str = None, source: str = "manual", raw_text: str = None):
    with get_connection() as conn:
        inv = conn.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        if not inv:
            raise ValueError(f"Invoice ID {invoice_id} not found.")

        p_date = payment_date or str(date.today())
        cur = conn.execute("""
            INSERT INTO payments (invoice_id, amount, transaction_id, payment_date, source, raw_text)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (invoice_id, amount, transaction_id, p_date, source, raw_text))

        total = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE invoice_id=?", (invoice_id,)
        ).fetchone()[0]

        status = "Paid" if total >= inv["amount"] else inv["status"]
        conn.execute("UPDATE invoices SET status=? WHERE id=?", (status, invoice_id))
        conn.commit()

        new_pmt = conn.execute("SELECT * FROM payments WHERE id=?", (cur.lastrowid,)).fetchone()

        return {
            "payment_id": cur.lastrowid,
            "invoice_id": invoice_id,
            "amount": amount,
            "total_paid": total,
            "invoice_amount": inv["amount"],
            "status": status,
            "payment": dict(new_pmt)
        }

def payment_history():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("""
            SELECT p.*, i.description AS invoice_description, c.name AS client_name
            FROM payments p
            JOIN invoices i ON i.id=p.invoice_id
            JOIN clients c ON c.id=i.client_id
            ORDER BY p.id DESC
        """).fetchall()]
