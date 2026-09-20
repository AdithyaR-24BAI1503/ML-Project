from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from .database import init_db
from .payment_service import record_payment, payment_history, list_invoices
from .ocr import extract_payment_data

app = FastAPI(title="ChatBiz — Sprint 4", version="4.0")

class PaymentRequest(BaseModel):
    invoice_id: int
    amount: float = Field(gt=0)
    transaction_id: str | None = None
    payment_date: str | None = None

@app.on_event("startup")
def startup():
    init_db()

@app.get("/api/invoices")
def invoices():
    return list_invoices()

@app.get("/api/payments")
def payments():
    return payment_history()

@app.post("/api/payments")
def payment(body: PaymentRequest):
    try:
        return record_payment(body.invoice_id, body.amount, body.transaction_id, body.payment_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/payments/ocr")
async def payment_ocr(invoice_id: int, screenshot: UploadFile = File(...)):
    tmp = Path("payment_screenshot")
    tmp.write_bytes(await screenshot.read())
    try:
        extracted = extract_payment_data(tmp)
        if extracted["amount"] is None:
            return {"message": "OCR completed but payment amount was not detected.", "ocr": extracted}
        try:
            result = record_payment(invoice_id, extracted["amount"], extracted["transaction_id"],
                                    source="ocr", raw_text=extracted["raw_text"])
            return {"message": "Payment OCR processed and invoice updated.", "ocr": extracted, "payment": result}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    finally:
        tmp.unlink(missing_ok=True)
