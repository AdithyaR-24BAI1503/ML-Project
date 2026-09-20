# ChatBiz

A WhatsApp-first AI-powered business management system for Indian micro and small enterprises.

Reg No: 24BAI1503 · Name: Adithya R

## Status: Sprint 1 (Weeks 1–2)

Per the sprint plan in Lab 1/Lab 3: **bot setup, user registration flow, database schema.**

This commit delivers:
- Database schema — SQLAlchemy models for all 8 entities from the Lab 4 ER Diagram (`app/models.py`), with the 1:M relationships exactly as designed (User → Client, User → Invoice, Invoice → InvoiceItem, Invoice → Payment, Invoice → Reminder, User → RecurringInvoice, Client → RecurringInvoice, User → Message).
- A FastAPI skeleton (`app/main.py`) representing the REST API Server component of the Gateway Layer from the Lab 3 architecture diagram.
- A working user registration endpoint (`POST /users/register`), the first functional requirement from Lab 1.
- Tests for the registration flow (`tests/test_users.py`).

WhatsApp webhook handling, NLP intent parsing, OCR, invoice PDF generation, and reminders are out of scope for this sprint — they land in Sprints 2–5 per the plan.

## Project structure

```
chatbiz/
├── app/
│   ├── main.py          # FastAPI app entrypoint
│   ├── database.py       # SQLAlchemy engine/session setup
│   ├── models.py         # ORM models (matches Lab 4 ERD)
│   ├── schemas.py        # Pydantic request/response schemas
│   └── routers/
│       └── users.py      # Registration + lookup endpoints
├── tests/
│   └── test_users.py
├── requirements.txt
├── .env.example
└── .gitignore
```

## Running locally

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env

uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000/docs for the interactive Swagger UI — you can try `POST /users/register` directly from there.

## Running tests

```bash
pytest
```

## Tech stack (per Lab 1 Software Requirements)

- **Backend:** Python 3.11, FastAPI
- **Database:** SQLite (dev, this sprint) → PostgreSQL (production)
- **ORM:** SQLAlchemy
- **Testing:** Pytest

## Roadmap (from Lab 1 sprint plan)

| Sprint | Weeks | Deliverables | Status |
|---|---|---|---|
| 1 | 1–2 | Bot setup, user registration, database schema | ✅ In progress (this commit) |
| 2 | 3–4 | NLP command parsing, client management | Planned |
| 3 | 5–6 | Invoice generation engine, PDF delivery | Planned |
| 4 | 7–8 | Payment tracking, UPI screenshot OCR | Planned |
| 5 | 9–10 | Automated reminders, voice input, recurring invoices | Planned |
| 6 | 11–12 | Analytics engine, web dashboard, testing, deployment | Planned |
