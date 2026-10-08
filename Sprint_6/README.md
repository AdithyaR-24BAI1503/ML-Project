# ChatBiz — Sprint 6
## Executive Business Analytics, REST JSON API & Standalone Frontend

This release completes Sprint 6 by introducing realistic Indian MSME sample data in `chatbiz.db`, converting all backend responses from HTML to structured REST **JSON**, providing CORS-enabled API endpoints, and delivering a standalone, modern frontend dashboard that runs independently from the backend.

---

## 🚀 Running Frontend & Backend Separately

You can run both services independently in two terminal windows:

### 1. Start the Backend API Server (Port 8000)

**PowerShell / Command Prompt:**
```powershell
cd Sprint_6
python -m uvicorn app.main:app --port 8000 --reload
```
*Or simply double-click / run `run_backend.bat` or `run_backend.ps1`.*

- **Backend API Base**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **OpenAPI JSON Spec**: `http://127.0.0.1:8000/openapi.json`

### 2. Start the Standalone Frontend Dashboard (Port 3000)

In a separate terminal:
```powershell
cd Sprint_6
python -m http.server 3000 --directory frontend
```
*Or simply double-click / run `run_frontend.bat` or `run_frontend.ps1`.*

- **Frontend URL**: `http://127.0.0.1:3000`

---

## 📊 Sample Database (`chatbiz.db`)

The database comes pre-seeded with realistic MSME profiles, diverse invoice statuses, payment records, reminders, and voice logs.

To re-seed or reset sample data at any time:
```powershell
cd Sprint_6
python seed_db.py --reset
```

### Pre-Seeded Entities:
- **8 Clients**: Ramesh Kumar (Kirana), Priya Sharma (Bakery), Amit Patel (Web Dev), Ananya Rao (Tutoring), Rajesh Singh (Transport), Sunita Verma (Boutique), Vikram Malhotra (Media), Deepak Mehta (Wholesale Electricals).
- **16 Invoices**: Spanning `Paid`, `Pending`, and `Overdue` statuses with due dates, descriptions, and UPI IDs.
- **7 Payments**: Logged with transaction references (`UPI`, `OCR screenshot scan`, `manual`).
- **8 Reminders**: Schedules for upcoming, due-today, and overdue payment alerts.
- **6 Voice Commands**: Natural language transcripts and classified intents.

---

## 🔌 REST JSON Endpoints

All backend endpoints return standard **JSON**:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API status and endpoint directory (JSON) |
| `GET` | `/api/analytics` | Overall KPIs, collection rate %, and client leaderboard |
| `GET` | `/api/clients` | List all clients with revenue totals and invoice counts |
| `POST` | `/api/clients` | Register a new client (`name`, `phone`, `email`) |
| `GET` | `/api/clients/{id}` | Client profile and associated invoices |
| `GET` | `/api/invoices` | List invoices with client details (supports `?status=` and `?search=`) |
| `POST` | `/api/invoices` | Issue a new invoice |
| `PATCH` | `/api/invoices/{id}/status` | Update invoice status (`Paid`, `Pending`, `Overdue`) |
| `POST` | `/api/invoices/{id}/mark-paid` | Mark invoice as Paid and log payment settlement |
| `GET` | `/api/payments` | Audit ledger of all payment transactions |
| `POST` | `/api/payments` | Record new payment settlement |
| `GET` | `/api/reminders` | Payment reminder schedules |
| `POST` | `/api/reminders/{id}/send` | Simulate WhatsApp reminder delivery |
| `GET` | `/api/voice-commands` | Speech-to-text transcripts & classified intents |
| `POST` | `/api/voice-commands` | Log voice command |
| `POST` | `/api/db/seed` | Trigger sample data seeding (`?force=true` to reset) |
| `GET` | `/api/export/invoices` | Stream CSV export of all invoices |

---

## 🧪 Automated Testing

To run the automated test suite:
```powershell
$env:PYTHONPATH="Sprint_6"; pytest Sprint_6
```
