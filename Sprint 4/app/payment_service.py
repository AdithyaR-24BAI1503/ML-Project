from datetime import date
from .database import get_connection

def list_invoices():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute('''
            SELECT i.*, c.name AS client_name
            FROM invoices i JOIN clients c ON c.id=i.client_id
            ORDER BY i.id DESC''').fetchall()]

def record_payment(invoice_id, amount, transaction_id=None, payment_date=None, source="manual", raw_text=None):
    with get_connection() as conn:
        inv = conn.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        if not inv:
            raise ValueError("Invoice not found.")
        cur = conn.execute('''INSERT INTO payments
            (invoice_id, amount, transaction_id, payment_date, source, raw_text)
            VALUES (?,?,?,?,?,?)''',
            (invoice_id, amount, transaction_id, payment_date or str(date.today()), source, raw_text))
        total = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM payments WHERE invoice_id=?", (invoice_id,)
        ).fetchone()[0]
        status = "Paid" if total >= inv["amount"] else "Pending"
        conn.execute("UPDATE invoices SET status=? WHERE id=?", (status, invoice_id))
        conn.commit()
        return {"payment_id": cur.lastrowid, "invoice_id": invoice_id,
                "total_paid": total, "invoice_amount": inv["amount"], "status": status}

def payment_history():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute('''
            SELECT p.*, i.description, c.name AS client_name
            FROM payments p JOIN invoices i ON i.id=p.invoice_id
            JOIN clients c ON c.id=i.client_id ORDER BY p.id DESC''').fetchall()]
