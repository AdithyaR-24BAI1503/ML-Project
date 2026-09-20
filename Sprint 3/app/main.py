from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from .database import init_db
from . import invoice_service
from .pdf_generator import generate_invoice_pdf

app = FastAPI(title="ChatBiz — Sprint 3", version="3.0")

class InvoiceRequest(BaseModel):
    client_id: int
    description: str = Field(min_length=1)
    amount: float = Field(gt=0)
    due_date: str
    upi_id: str | None = None

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(open("app/static/index.html", encoding="utf-8").read())

@app.get("/api/invoices")
def invoices():
    return invoice_service.list_invoices()

@app.post("/api/invoices")
def create_invoice(body: InvoiceRequest):
    try:
        invoice = invoice_service.create_invoice(
            body.client_id, body.description, body.amount,
            body.due_date, body.upi_id
        )
        path = generate_invoice_pdf(invoice)
        invoice_service.save_pdf_path(invoice["id"], path)
        return {
            "message": "Invoice created and PDF generated.",
            "invoice": invoice,
            "download_url": f"/api/invoices/{invoice['id']}/pdf"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/invoices/{invoice_id}/pdf")
def invoice_pdf(invoice_id: int):
    invoice = invoice_service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    path = invoice.get("pdf_path")
    if not path or not Path(path).exists():
        path = generate_invoice_pdf(invoice)
        invoice_service.save_pdf_path(invoice_id, path)
    return FileResponse(path, media_type="application/pdf",
                        filename=f"invoice_{invoice_id}.pdf")

@app.post("/api/invoices/{invoice_id}/send")
def send_invoice(invoice_id: int):
    invoice = invoice_service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return {
        "status": "SIMULATED_SENT",
        "channel": "WhatsApp Business (mock)",
        "recipient": invoice.get("client_phone"),
        "invoice_id": invoice_id,
        "message": "PDF invoice delivery simulated successfully."
    }
