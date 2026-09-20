# ChatBiz — Sprint 4
## Payment Tracking + UPI Screenshot OCR

Implements the documented Sprint 4 deliverables:
- Payment tracking
- UPI payment screenshot OCR
- Payment matching to outstanding invoices
- Invoice status updates: Pending / Paid / Overdue

WhatsApp permissions are not required. Screenshots can be uploaded directly through the demo UI/API.

## Run
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

Open http://127.0.0.1:8000/docs
