import csv, io
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from .database import init_db, get_connection
from .analytics import summary, client_summary

app = FastAPI(title="ChatBiz — Sprint 6", version="6.0")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def dashboard():
    s = summary()
    rows = client_summary()
    table = "".join(f"<tr><td>{r['name']}</td><td>{r['invoices']}</td><td>Rs. {r['total_invoiced']:.2f}</td><td>Rs. {r['paid']:.2f}</td></tr>" for r in rows)
    return f'''<!doctype html><html><head><title>ChatBiz Dashboard</title>
    <style>body{{font-family:Arial;max-width:1000px;margin:40px auto}}.card{{display:inline-block;padding:18px;margin:6px;background:#f3f3f3;border-radius:8px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;border:1px solid #ddd}}</style>
    </head><body><h1>ChatBiz Analytics Dashboard</h1>
    <div class="card">Clients<br><b>{s["client_count"]}</b></div>
    <div class="card">Invoices<br><b>{s["invoice_count"]}</b></div>
    <div class="card">Invoiced<br><b>Rs. {s["total_invoiced"]:.2f}</b></div>
    <div class="card">Paid<br><b>Rs. {s["paid_amount"]:.2f}</b></div>
    <div class="card">Pending<br><b>Rs. {s["pending_amount"]:.2f}</b></div>
    <p><a href="/api/export/invoices">Export invoices CSV</a></p>
    <h2>Client Summary</h2><table><tr><th>Client</th><th>Invoices</th><th>Total</th><th>Paid</th></tr>{table}</table>
    </body></html>'''

@app.get("/api/analytics")
def analytics():
    return {"overall": summary(), "clients": client_summary()}

@app.get("/api/export/invoices")
def export_invoices():
    with get_connection() as c:
        rows = c.execute("SELECT * FROM invoices ORDER BY id").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id","client_id","description","amount","status","due_date"])
    writer.writerows([tuple(r) for r in rows])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=invoices.csv"})
