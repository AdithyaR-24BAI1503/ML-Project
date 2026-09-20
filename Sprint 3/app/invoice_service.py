from .database import get_connection

def create_invoice(client_id, description, amount, due_date, upi_id=None):
    with get_connection() as conn:
        client = conn.execute(
            "SELECT * FROM clients WHERE id=?", (client_id,)
        ).fetchone()
        if not client:
            raise ValueError("Client not found.")
        cur = conn.execute(
            """INSERT INTO invoices(client_id, description, amount, due_date, upi_id)
               VALUES (?, ?, ?, ?, ?)""",
            (client_id, description, amount, due_date, upi_id)
        )
        conn.commit()
        row = conn.execute("""
            SELECT i.*, c.name AS client_name, c.phone AS client_phone
            FROM invoices i JOIN clients c ON c.id=i.client_id WHERE i.id=?
        """, (cur.lastrowid,)).fetchone()
        return dict(row)

def get_invoice(invoice_id):
    with get_connection() as conn:
        row = conn.execute("""
            SELECT i.*, c.name AS client_name, c.phone AS client_phone,
                   c.email AS client_email
            FROM invoices i JOIN clients c ON c.id=i.client_id WHERE i.id=?
        """, (invoice_id,)).fetchone()
        return dict(row) if row else None

def list_invoices():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("""
            SELECT i.*, c.name AS client_name
            FROM invoices i JOIN clients c ON c.id=i.client_id
            ORDER BY i.id DESC
        """).fetchall()]

def save_pdf_path(invoice_id, path):
    with get_connection() as conn:
        conn.execute(
            "UPDATE invoices SET pdf_path=? WHERE id=?", (str(path), invoice_id)
        )
        conn.commit()
