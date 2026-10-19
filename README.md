# ChatBiz — WhatsApp-First MSME Business Management System

ChatBiz is an AI-powered business management platform tailored for Indian MSMEs (freelancers, tutors, kirana store owners, and service providers). It streamlines customer onboarding, UPI-linked invoicing, payment settlement with OCR extraction, automated WhatsApp reminders, voice assistant operations, and real-time executive financial analytics.

---

## 📌 Features

- **Executive Analytics Dashboard**: Real-time telemetry on total revenue, collected payments, pending receivables, overdue exposure, and collection rates.
- **Client CRM**: Manage customer contacts, invoice counts, and payment ledgers.
- **UPI Invoicing & PDF Generation**: Generates PDF invoices with embedded UPI dynamic payment QR codes (scan-and-pay via GPay, PhonePe, Paytm).
- **Payment Settlement & OCR**: Record manual payments, UPI webhook settlements, or upload payment receipts to extract transaction ID and amount automatically via OCR.
- **WhatsApp Reminders Engine**: Automated 3-stage reminders (`BEFORE_DUE`, `DUE_TODAY`, `OVERDUE`) with simulated WhatsApp Business API delivery.
- **Voice Command Assistant**: Spoken / typed natural language interface powered by intent classification and Web Speech API.
- **CSV Data Export**: Instant streaming export of all business invoices.

---

## 🏗️ Project Architecture

```
chatbiz/
├── app/
│   ├── __init__.py          # Unified application package
│   ├── main.py              # FastAPI endpoints uniting all business domains
│   ├── database.py          # Unified SQLite database engine & session provider
│   ├── models.py            # SQLAlchemy relational ORM models
│   ├── schemas.py           # Pydantic request/response validation schemas
│   ├── analytics.py         # Financial calculation & leaderboard algorithms
│   ├── pdf_generator.py     # PDF generation with ReportLab & UPI QR code
│   ├── ocr.py               # Payment screenshot OCR extraction
│   ├── nlp.py               # Natural language parser for onboarding & clients
│   ├── reminders.py         # WhatsApp payment reminders scheduler & runner
│   ├── voice.py             # Voice transcription & intent classification
│   ├── seed_data.py         # MSME sample dataset seeder
│   └── services/            # Domain service logic
│       ├── __init__.py
│       ├── client_service.py
│       ├── invoice_service.py
│       └── payment_service.py
├── frontend/
│   ├── index.html           # Minimalist Executive Ledger dashboard (Stitch-designed)
│   ├── styles.css           # Clean, professional B2B styling (Inter typography, no neon glow)
│   └── app.js               # Reactive frontend client application
├── tests/
│   ├── __init__.py
│   ├── test_api.py          # Core REST API & analytics test suite
│   ├── test_users.py        # User onboarding & registration tests
│   ├── test_nlp.py          # NLP command parsing tests
│   ├── test_invoices.py     # Invoice creation, status, and PDF tests
│   ├── test_payments.py     # Payment recording & settlement tests
│   └── test_reminders.py    # Reminder scheduling & voice intent tests
├── requirements.txt         # Consolidated Python dependencies
├── Dockerfile               # Production container definition
├── run_backend.bat          # Easy backend launcher script (Windows CMD)
├── run_backend.ps1          # Easy backend launcher script (PowerShell)
├── run_frontend.bat         # Easy frontend launcher script (Windows CMD)
└── run_frontend.ps1         # Easy frontend launcher script (PowerShell)
```

---

## ⚙️ Quick Start

### 1. Installation

Install all required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Launch the Backend API Server

Using Python directly:
```bash
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Or use the launcher script:
```bash
./run_backend.bat
```
The API server starts at **`http://127.0.0.1:8000`** with interactive Swagger documentation at **`http://127.0.0.1:8000/docs`**.

### 3. Launch the Frontend Dashboard

Run the local web server:
```bash
py -m http.server 3000 --directory frontend
```
Or use the launcher script:
```bash
./run_frontend.bat
```
Open **`http://127.0.0.1:3000`** in any modern web browser (or directly open `frontend/index.html` or visit `http://127.0.0.1:8000/dashboard`).

---

## 🧪 Running Automated Tests

Run the full unified test suite across all modules:

```bash
py -m pytest -v tests
```

---

## 🐳 Docker Deployment

To build and run the complete ChatBiz application via Docker:

```bash
docker build -t chatbiz .
docker run -p 8000:8000 chatbiz
```

---

## 📄 License
Academic & SE Lab Project Implementation.
