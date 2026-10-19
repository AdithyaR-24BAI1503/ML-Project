"""
ChatBiz Business Analytics Module
Calculates real-time financial telemetry, revenue, receivables, and MSME client metrics.
"""
from .database import get_connection

def summary():
    """Returns high-level business financial KPIs across all invoices."""
    with get_connection() as c:
        total = c.execute("SELECT COALESCE(SUM(amount), 0) FROM invoices").fetchone()[0]
        paid = c.execute("SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE status='Paid'").fetchone()[0]
        pending = c.execute("SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE status='Pending'").fetchone()[0]
        overdue = c.execute("SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE status='Overdue'").fetchone()[0]
        clients = c.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        invoice_count = c.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
        paid_count = c.execute("SELECT COUNT(*) FROM invoices WHERE status='Paid'").fetchone()[0]
        pending_count = c.execute("SELECT COUNT(*) FROM invoices WHERE status='Pending'").fetchone()[0]
        overdue_count = c.execute("SELECT COUNT(*) FROM invoices WHERE status='Overdue'").fetchone()[0]
        collection_rate = round((paid / total * 100), 1) if total > 0 else 0.0

    return {
        "total_invoiced": total,
        "paid_amount": paid,
        "pending_amount": pending,
        "overdue_amount": overdue,
        "client_count": clients,
        "invoice_count": invoice_count,
        "paid_count": paid_count,
        "pending_count": pending_count,
        "overdue_count": overdue_count,
        "collection_rate_pct": collection_rate
    }

def client_summary():
    """Returns ranked client ledger summaries with total invoiced, paid, and pending balances."""
    with get_connection() as c:
        rows = c.execute("""
            SELECT c.id, c.name, c.phone, c.email,
                   COUNT(i.id) AS invoices,
                   COALESCE(SUM(i.amount), 0) AS total_invoiced,
                   COALESCE(SUM(CASE WHEN i.status='Paid' THEN i.amount ELSE 0 END), 0) AS paid,
                   COALESCE(SUM(CASE WHEN i.status!='Paid' THEN i.amount ELSE 0 END), 0) AS pending
            FROM clients c
            LEFT JOIN invoices i ON i.client_id = c.id
            GROUP BY c.id
            ORDER BY total_invoiced DESC
        """).fetchall()
        return [dict(r) for r in rows]
