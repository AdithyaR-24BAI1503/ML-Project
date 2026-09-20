# ChatBiz — Sprint 3
## Invoice Generation + PDF Delivery

Implements the Sprint 3 deliverables:
- Invoice creation
- ReportLab PDF generation
- Invoice database table
- UPI QR code
- Invoice listing
- Simulated WhatsApp PDF delivery
- Simple demo UI

WhatsApp Business permissions/API credentials are intentionally skipped.
`POST /api/invoices/{id}/send` is a mock delivery endpoint for the review.

### Run
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 or http://127.0.0.1:8000/docs

### Demo payload
```json
{
  "client_id": 1,
  "description": "June coaching",
  "amount": 5000,
  "due_date": "2026-10-01",
  "upi_id": "merchant@upi"
}
```
