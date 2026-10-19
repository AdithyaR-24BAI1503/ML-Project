"""
Invoice Management Business Service
"""
from ..database import get_connection

def create_invoice(client_id: int, description: str, amount: float, due_date: str, upi_id: str = None, recurring: int = 0, recurrence: str = None):
    with get_connection() as conn:
        client = conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
        if not client:
            raise ValueError(f"Client ID {client_id} not found.")

        cur = conn.execute("""
            INSERT INTO invoices(client_id, description, amount, due_date, upi_id, recurring, recurrence, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (client_id, description.strip(), amount, due_date, upi_id, recurring, recurrence))
        conn.commit()
        new_id = cur.lastrowid

        row = conn.execute("""
            SELECT i.*, c.name AS client_name, c.phone AS client_phone, c.email AS client_email
            FROM invoices i JOIN clients c ON c.id=i.client_id WHERE i.id=?
        """, (new_id,)).fetchone()
        return dict(row)

def get_invoice(invoice_id: int):
    with get_connection() as conn:
        row = conn.execute("""
            SELECT i.*, c.name AS client_name, c.phone AS client_phone, c.email AS client_email
            FROM invoices i JOIN clients c ON c.id=i.client_id WHERE i.id=?
        """, (invoice_id,)).fetchone()
        return dict(row) if row else None

def list_invoices():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("""
            SELECT i.*, c.name AS client_name, c.phone AS client_phone, c.email AS client_email
            FROM invoices i JOIN clients c ON c.id=i.client_id
            ORDER BY i.id DESC
        """).fetchall()]

def save_pdf_path(invoice_id: int, path: str):
    with get_connection() as conn:
        conn.execute("UPDATE invoices SET pdf_path=? WHERE id=?", (str(path), invoice_id))
        conn.commit()
