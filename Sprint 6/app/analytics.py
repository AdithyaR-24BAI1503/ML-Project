from .database import get_connection

def summary():
    with get_connection() as c:
        total = c.execute("SELECT COALESCE(SUM(amount),0) FROM invoices").fetchone()[0]
        paid = c.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status='Paid'").fetchone()[0]
        pending = c.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status='Pending'").fetchone()[0]
        overdue = c.execute("SELECT COALESCE(SUM(amount),0) FROM invoices WHERE status='Overdue'").fetchone()[0]
        clients = c.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        invoice_count = c.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
    return {"total_invoiced": total, "paid_amount": paid, "pending_amount": pending,
            "overdue_amount": overdue, "client_count": clients, "invoice_count": invoice_count}

def client_summary():
    with get_connection() as c:
        return [dict(r) for r in c.execute('''
            SELECT c.name, COUNT(i.id) invoices,
                   COALESCE(SUM(i.amount),0) total_invoiced,
                   COALESCE(SUM(CASE WHEN i.status='Paid' THEN i.amount ELSE 0 END),0) paid
            FROM clients c LEFT JOIN invoices i ON i.client_id=c.id
            GROUP BY c.id ORDER BY total_invoiced DESC''').fetchall()]
