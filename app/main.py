"""
ChatBiz — WhatsApp-First MSME Business Management System
Unified API Application (Uniting Sprints 1 through 6)
"""
import csv
import difflib
import io
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import init_db, get_connection, get_db
from .analytics import summary, client_summary
from .seed_data import seed_sample_data
from .pdf_generator import generate_invoice_pdf
from .ocr import extract_payment_data
from .nlp import parse_command
from .reminders import seed_invoice_reminders, run_due_reminders
from .voice import transcribe_demo, classify_voice_command
from .chat import (
    handle_client_message,
    handle_manager_message,
    get_chat_history,
    clear_chat_history,
    save_chat_message
)
from . import models, schemas
from .schemas import (
    UserRegisterRequest,
    UserResponse,
    ClientCreate,
    ClientUpdate,
    InvoiceCreate,
    InvoiceStatusUpdate,
    PaymentCreate,
    VoiceCommandCreate,
    VoiceDemo,
    RecurringInvoiceCreate,
    ClientChatRequest,
    ManagerChatRequest,
    ClearChatRequest,
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
GENERATED_DIR = BASE_DIR / "generated_invoices"
GENERATED_DIR.mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="ChatBiz — MSME Business Management API",
    version="6.0.0",
    description="WhatsApp-First MSME Business Management System uniting CRM, UPI Invoicing, OCR Payments, Reminders, Voice AI, and Analytics.",
    lifespan=lifespan
)

# Enable CORS for external origins and local dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static assets if available
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# ---------------------------------------------------------
# Health & Root Endpoints
# ---------------------------------------------------------
@app.get("/health")
def health_check():
    """Health check endpoint for container and platform monitoring."""
    return {"status": "healthy"}


@app.get("/")
def api_root():
    """Root metadata endpoint describing system status and available endpoints."""
    return {
        "app": "ChatBiz Business Management API",
        "status": "online",
        "version": "6.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "dashboard": "/dashboard",
            "health": "/health",
            "analytics": "/api/analytics",
            "clients": "/api/clients",
            "invoices": "/api/invoices",
            "payments": "/api/payments",
            "reminders": "/api/reminders",
            "voice_commands": "/api/voice-commands",
            "users": "/users",
            "export_invoices": "/api/export/invoices",
            "docs": "/docs"
        }
    }


@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    """Directly serves the executive MSME frontend dashboard."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Frontend dashboard not found.</h1>", status_code=404)


# ---------------------------------------------------------
# User Onboarding & Registration Endpoints (Sprint 1)
# ---------------------------------------------------------
@app.post("/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@app.post("/api/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """Registers a new business owner keyed by their WhatsApp phone number."""
    existing = db.query(models.User).filter(models.User.phone_whatsapp == payload.phone_whatsapp).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this WhatsApp number is already registered."
        )

    user = models.User(
        name=payload.name,
        phone_whatsapp=payload.phone_whatsapp,
        business_name=payload.business_name,
        gst_number=payload.gst_number,
        subscription_plan="free"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/{phone_whatsapp}", response_model=UserResponse)
@app.get("/api/users/{phone_whatsapp}", response_model=UserResponse)
def get_user_by_phone(phone_whatsapp: str, db: Session = Depends(get_db)):
    """Looks up registered business owner profile by WhatsApp phone number."""
    user = db.query(models.User).filter(models.User.phone_whatsapp == phone_whatsapp).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


# ---------------------------------------------------------
# Business Analytics Endpoints (Sprint 6)
# ---------------------------------------------------------
@app.get("/api/analytics")
def get_analytics():
    """Returns high-level business financial KPIs and client performance summaries."""
    return {
        "overall": summary(),
        "clients": client_summary()
    }


# ---------------------------------------------------------
# Clients Directory Endpoints (Sprint 2 & 6)
# ---------------------------------------------------------
@app.get("/api/clients")
def list_clients():
    """Returns list of clients joined with calculated invoice and receivables totals."""
    with get_connection() as c:
        rows = c.execute("""
            SELECT c.id, c.name, c.phone, c.email, c.address, c.notes, c.created_at,
                   COUNT(i.id) AS invoices_count,
                   COALESCE(SUM(i.amount), 0) AS total_invoiced,
                   COALESCE(SUM(CASE WHEN i.status='Paid' THEN i.amount ELSE 0 END), 0) AS paid_amount,
                   COALESCE(SUM(CASE WHEN i.status!='Paid' THEN i.amount ELSE 0 END), 0) AS pending_amount
            FROM clients c
            LEFT JOIN invoices i ON i.client_id = c.id
            GROUP BY c.id
            ORDER BY c.name ASC
        """).fetchall()
        return [dict(r) for r in rows]


@app.post("/api/clients", status_code=status.HTTP_201_CREATED)
def create_client(client: ClientCreate):
    """Registers a new MSME client profile."""
    with get_connection() as c:
        try:
            cur = c.execute(
                "INSERT INTO clients (name, phone, email, address, notes) VALUES (?, ?, ?, ?, ?)",
                (client.name.strip(), client.phone, client.email, client.address, client.notes)
            )
            c.commit()
            new_client = c.execute("SELECT * FROM clients WHERE id=?", (cur.lastrowid,)).fetchone()
            return {"message": "Client created successfully", "client": dict(new_client)}
        except Exception as e:
            if "UNIQUE constraint failed" in str(e) or "UNIQUE" in str(e).upper():
                raise HTTPException(status_code=400, detail="A client with this name already exists.")
            raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/clients/{client_id}")
def get_client_details(client_id: int):
    """Returns single client profile and ledger of their invoices."""
    with get_connection() as c:
        client = c.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")
        invoices = c.execute("SELECT * FROM invoices WHERE client_id=? ORDER BY id DESC", (client_id,)).fetchall()
        return {
            "client": dict(client),
            "invoices": [dict(i) for i in invoices]
        }


@app.patch("/api/clients/{client_id}")
def update_client(client_id: int, body: ClientUpdate):
    """Updates client contact info."""
    with get_connection() as c:
        client = c.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")
        updates = []
        params = []
        if body.phone is not None:
            updates.append("phone=?")
            params.append(body.phone)
        if body.email is not None:
            updates.append("email=?")
            params.append(body.email)
        if body.address is not None:
            updates.append("address=?")
            params.append(body.address)
        if body.notes is not None:
            updates.append("notes=?")
            params.append(body.notes)
        if updates:
            params.append(client_id)
            c.execute(f"UPDATE clients SET {', '.join(updates)} WHERE id=?", params)
            c.commit()
        updated = c.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
        return {"message": "Client updated successfully", "client": dict(updated)}


@app.delete("/api/clients/{client_id}")
def delete_client(client_id: int):
    """Deletes client profile and cascading records."""
    with get_connection() as c:
        cur = c.execute("DELETE FROM clients WHERE id=?", (client_id,))
        c.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Client not found.")
        return {"message": f"Client ID {client_id} deleted successfully."}


# ---------------------------------------------------------
# Invoices Endpoints (Sprint 3 & 6)
# ---------------------------------------------------------
@app.get("/api/invoices")
def list_invoices(
    status: Optional[str] = Query(None, description="Filter by status: Paid, Pending, or Overdue"),
    search: Optional[str] = Query(None, description="Search by client name or description")
):
    """Returns invoice ledger with optional status and search keyword filters."""
    query = """
        SELECT i.id, i.client_id, i.description, i.amount, i.due_date, i.upi_id,
               i.status, i.pdf_path, i.recurring, i.recurrence, i.created_at,
               c.name AS client_name, c.phone AS client_phone, c.email AS client_email
        FROM invoices i
        JOIN clients c ON i.client_id = c.id
        WHERE 1=1
    """
    params = []
    if status and status.lower() != "all":
        query += " AND LOWER(i.status) = LOWER(?)"
        params.append(status)
    if search:
        query += " AND (LOWER(i.description) LIKE LOWER(?) OR LOWER(c.name) LIKE LOWER(?))"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY i.id DESC"

    with get_connection() as c:
        rows = c.execute(query, params).fetchall()
        return [dict(r) for r in rows]


@app.post("/api/invoices", status_code=status.HTTP_201_CREATED)
def create_invoice(invoice: InvoiceCreate):
    """Creates a new invoice, automatically generates PDF with UPI QR code, and queues reminders."""
    with get_connection() as c:
        client = c.execute("SELECT * FROM clients WHERE id=?", (invoice.client_id,)).fetchone()
        if not client:
            raise HTTPException(status_code=404, detail=f"Client ID {invoice.client_id} does not exist.")

        cur = c.execute("""
            INSERT INTO invoices (client_id, description, amount, due_date, upi_id, recurring, recurrence, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (
            invoice.client_id, invoice.description.strip(), invoice.amount,
            invoice.due_date, invoice.upi_id or "chatbiz.merchant@upi",
            invoice.recurring, invoice.recurrence
        ))
        c.commit()
        new_id = cur.lastrowid

        # Schedule reminder
        seed_invoice_reminders(new_id, invoice.due_date)

        row = c.execute("""
            SELECT i.*, c.name AS client_name, c.phone AS client_phone, c.email AS client_email
            FROM invoices i JOIN clients c ON i.client_id = c.id
            WHERE i.id=?
        """, (new_id,)).fetchone()
        inv_dict = dict(row)

        # Generate PDF with QR code
        try:
            pdf_path = generate_invoice_pdf(inv_dict)
            c.execute("UPDATE invoices SET pdf_path=? WHERE id=?", (str(pdf_path), new_id))
            c.commit()
            inv_dict["pdf_path"] = str(pdf_path)
        except Exception as e:
            print(f"Warning: PDF generation failed: {e}")

        return {
            "message": "Invoice created and PDF generated successfully.",
            "invoice": inv_dict,
            "download_url": f"/api/invoices/{new_id}/pdf"
        }


@app.get("/api/invoices/{invoice_id}")
def get_invoice(invoice_id: int):
    """Retrieves single invoice details joined with client info."""
    with get_connection() as c:
        row = c.execute("""
            SELECT i.*, c.name AS client_name, c.phone AS client_phone, c.email AS client_email
            FROM invoices i JOIN clients c ON i.client_id = c.id
            WHERE i.id=?
        """, (invoice_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Invoice not found.")
        return dict(row)


@app.patch("/api/invoices/{invoice_id}/status")
def update_invoice_status(invoice_id: int, body: InvoiceStatusUpdate):
    """Updates status of an invoice ('Paid', 'Pending', 'Overdue')."""
    valid = {"Paid", "Pending", "Overdue"}
    clean_status = body.status.capitalize()
    if clean_status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid}")

    with get_connection() as c:
        row = c.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Invoice not found.")
        c.execute("UPDATE invoices SET status=? WHERE id=?", (clean_status, invoice_id))
        c.commit()
        updated = c.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        return {"message": f"Invoice status updated to {clean_status}", "invoice": dict(updated)}


@app.post("/api/invoices/{invoice_id}/mark-paid")
def mark_invoice_paid(invoice_id: int):
    """Marks an invoice as Paid and logs a settlement payment record."""
    with get_connection() as c:
        inv = c.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        c.execute("UPDATE invoices SET status='Paid' WHERE id=?", (invoice_id,))
        existing_pmt = c.execute("SELECT id FROM payments WHERE invoice_id=?", (invoice_id,)).fetchone()
        if not existing_pmt:
            today_str = datetime.now().strftime("%Y-%m-%d")
            tx_id = f"MANUAL/{datetime.now().strftime('%Y%m%d')}/{invoice_id}"
            c.execute("""
                INSERT INTO payments (invoice_id, amount, transaction_id, payment_date, source, raw_text)
                VALUES (?, ?, ?, ?, 'manual', 'Marked as paid from ChatBiz dashboard')
            """, (invoice_id, inv["amount"], tx_id, today_str))

        c.commit()
        updated = c.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        return {"message": "Invoice marked as Paid", "invoice": dict(updated)}


@app.get("/api/invoices/{invoice_id}/pdf")
def invoice_pdf(invoice_id: int):
    """Generates on demand or serves the PDF invoice with embedded UPI payment QR code."""
    with get_connection() as c:
        row = c.execute("""
            SELECT i.*, c.name AS client_name, c.phone AS client_phone, c.email AS client_email
            FROM invoices i JOIN clients c ON i.client_id = c.id
            WHERE i.id=?
        """, (invoice_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        inv_dict = dict(row)
        pdf_path = inv_dict.get("pdf_path")
        if not pdf_path or not Path(pdf_path).exists():
            generated = generate_invoice_pdf(inv_dict)
            c.execute("UPDATE invoices SET pdf_path=? WHERE id=?", (str(generated), invoice_id))
            c.commit()
            pdf_path = str(generated)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"invoice_{invoice_id:04d}.pdf"
        )


@app.post("/api/invoices/{invoice_id}/send")
def send_invoice_whatsapp(invoice_id: int):
    """Simulates delivery of invoice PDF and UPI payment link via WhatsApp."""
    with get_connection() as c:
        row = c.execute("""
            SELECT i.*, c.name AS client_name, c.phone AS client_phone
            FROM invoices i JOIN clients c ON i.client_id = c.id
            WHERE i.id=?
        """, (invoice_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        return {
            "status": "SIMULATED_SENT",
            "channel": "WhatsApp Business API (simulated)",
            "recipient": row["client_phone"],
            "invoice_id": invoice_id,
            "amount": row["amount"],
            "message": f"Invoice #{invoice_id} PDF and payment link delivered to {row['client_name']} ({row['client_phone']})."
        }


@app.post("/api/recurring-invoices")
def create_recurring_invoice(body: RecurringInvoiceCreate):
    """Creates a recurring subscription invoice with automated reminder cadence."""
    with get_connection() as c:
        client = c.execute("SELECT id FROM clients WHERE id=?", (body.client_id,)).fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")

        cur = c.execute("""
            INSERT INTO invoices (client_id, description, amount, due_date, recurring, recurrence, status)
            VALUES (?, ?, ?, ?, 1, ?, 'Pending')
        """, (body.client_id, body.description, body.amount, body.due_date, body.recurrence))
        c.commit()
        inv_id = cur.lastrowid
        seed_invoice_reminders(inv_id, body.due_date)

        return {
            "message": "Recurring invoice created successfully.",
            "invoice_id": inv_id,
            "recurrence": body.recurrence
        }


# ---------------------------------------------------------
# Payments & OCR Endpoints (Sprint 4 & 6)
# ---------------------------------------------------------
@app.get("/api/payments")
def list_payments():
    """Returns settlement transaction audit ledger."""
    with get_connection() as c:
        rows = c.execute("""
            SELECT p.id, p.invoice_id, p.amount, p.transaction_id, p.payment_date,
                   p.source, p.raw_text, p.created_at,
                   i.description AS invoice_description,
                   c.name AS client_name
            FROM payments p
            LEFT JOIN invoices i ON p.invoice_id = i.id
            LEFT JOIN clients c ON i.client_id = c.id
            ORDER BY p.id DESC
        """).fetchall()
        return [dict(r) for r in rows]


@app.post("/api/payments", status_code=status.HTTP_200_OK)
def record_payment(payment: PaymentCreate):
    """Records payment settlement and updates invoice status to Paid when fully settled."""
    with get_connection() as c:
        inv = c.execute("SELECT * FROM invoices WHERE id=?", (payment.invoice_id,)).fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        p_date = payment.payment_date or str(date.today())
        tx_id = payment.transaction_id or f"TXN/{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cur = c.execute("""
            INSERT INTO payments (invoice_id, amount, transaction_id, payment_date, source, raw_text)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (payment.invoice_id, payment.amount, tx_id, p_date, payment.source, payment.raw_text))

        total_paid = c.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE invoice_id=?", (payment.invoice_id,)
        ).fetchone()[0]

        new_status = "Paid" if total_paid >= inv["amount"] else inv["status"]
        c.execute("UPDATE invoices SET status=? WHERE id=?", (new_status, payment.invoice_id))
        c.commit()

        new_pmt = c.execute("SELECT * FROM payments WHERE id=?", (cur.lastrowid,)).fetchone()

        return {
            "message": "Payment recorded successfully",
            "status": new_status,
            "total_paid": total_paid,
            "invoice_amount": inv["amount"],
            "payment": dict(new_pmt)
        }


@app.post("/api/payments/ocr")
async def payment_ocr(
    invoice_id: Optional[int] = Form(None),
    screenshot: UploadFile = File(...)
):
    """
    Scans uploaded payment screenshot using OCR, extracts transaction details and amount,
    and updates invoice if invoice_id is specified.
    """
    tmp_path = BASE_DIR / "temp_ocr_screenshot.png"
    tmp_path.write_bytes(await screenshot.read())
    try:
        extracted = extract_payment_data(tmp_path)
        result = None
        if invoice_id and extracted.get("amount"):
            with get_connection() as c:
                inv = c.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
                if inv:
                    cur = c.execute("""
                        INSERT INTO payments (invoice_id, amount, transaction_id, payment_date, source, raw_text)
                        VALUES (?, ?, ?, ?, 'ocr', ?)
                    """, (
                        invoice_id,
                        extracted["amount"],
                        extracted.get("transaction_id") or f"OCR/{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        str(date.today()),
                        extracted.get("raw_text")
                    ))
                    tot = c.execute("SELECT SUM(amount) FROM payments WHERE invoice_id=?", (invoice_id,)).fetchone()[0] or 0
                    if tot >= inv["amount"]:
                        c.execute("UPDATE invoices SET status='Paid' WHERE id=?", (invoice_id,))
                    c.commit()
                    new_pmt = c.execute("SELECT * FROM payments WHERE id=?", (cur.lastrowid,)).fetchone()
                    result = dict(new_pmt)

        return {
            "message": "Payment OCR processed successfully." if extracted.get("amount") else "OCR processed; amount not clearly recognized.",
            "ocr": extracted,
            "payment": result
        }
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------
# Reminders Endpoints (Sprint 5 & 6)
# ---------------------------------------------------------
@app.get("/api/reminders")
def list_reminders():
    """Returns scheduled WhatsApp payment reminders."""
    with get_connection() as c:
        rows = c.execute("""
            SELECT r.id, r.invoice_id, r.reminder_type, r.scheduled_for, r.status, r.sent_at, r.created_at,
                   i.description AS invoice_description, i.amount AS invoice_amount, i.due_date,
                   c.name AS client_name, c.phone AS client_phone
            FROM reminders r
            JOIN invoices i ON r.invoice_id = i.id
            JOIN clients c ON i.client_id = c.id
            ORDER BY r.id DESC
        """).fetchall()
        return [dict(r) for r in rows]


@app.post("/api/reminders/seed/{invoice_id}")
def seed_reminders(invoice_id: int, due_date: str = Query(...)):
    """Seeds automated payment reminders for an invoice."""
    seed_invoice_reminders(invoice_id, due_date)
    return {"message": "Reminder schedule created.", "invoice_id": invoice_id}


@app.post("/api/reminders/run")
def trigger_due_reminders():
    """Executes all due payment reminders."""
    dispatched = run_due_reminders()
    return {"sent": dispatched, "count": len(dispatched)}


@app.post("/api/reminders/{reminder_id}/send")
def send_single_reminder(reminder_id: int):
    """Simulates sending a specific scheduled WhatsApp reminder."""
    with get_connection() as c:
        row = c.execute("""
            SELECT r.*, c.name AS client_name, c.phone AS client_phone, i.amount
            FROM reminders r
            JOIN invoices i ON r.invoice_id = i.id
            JOIN clients c ON i.client_id = c.id
            WHERE r.id=?
        """, (reminder_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Reminder not found.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE reminders SET status='SENT', sent_at=? WHERE id=?", (now_str, reminder_id))
        c.commit()

        return {
            "status": "SENT",
            "reminder_id": reminder_id,
            "channel": "WhatsApp Business API (simulated)",
            "recipient": row["client_phone"],
            "client_name": row["client_name"],
            "amount": row["amount"],
            "message": f"WhatsApp reminder sent successfully to {row['client_name']} ({row['client_phone']})."
        }


# ---------------------------------------------------------
# Voice Commands & NLP (Sprint 1, 5 & 6)
# ---------------------------------------------------------
def resolve_client_from_transcript(transcript: str, conn, create_if_missing: bool = True):
    clients = conn.execute("SELECT id, name FROM clients").fetchall()
    if not clients and not create_if_missing:
        return None, None

    t_lower = transcript.lower()
    t_clean = re.sub(r'[^a-z0-9]', '', t_lower)

    candidate_match = re.search(
        r'(?:for|to|bill|from)\s+([A-Za-z\s\.\']+?)(?:\s+(?:of|for|amount|\d+|rupees|rs\.?|inr)\b|$)',
        transcript,
        flags=re.I
    )
    candidate_name = candidate_match.group(1).strip() if candidate_match else None
    if candidate_name and candidate_name.lower() in ["an invoice", "invoice", "a payment", "payment", "me", "him", "her"]:
        candidate_name = None

    for cl in clients:
        cl_clean = re.sub(r'\(.*?\)', '', cl["name"]).strip()
        cl_norm = re.sub(r'[^a-z0-9]', '', cl_clean.lower())
        if cl_norm and (cl_norm in t_clean or (len(t_clean) > 5 and t_clean in cl_norm)):
            return dict(cl), candidate_name

    if candidate_name:
        cand_norm = re.sub(r'[^a-z0-9]', '', candidate_name.lower())
        best_match = None
        best_ratio = 0.0
        for cl in clients:
            clean_name = re.sub(r'\(.*?\)', '', cl["name"]).strip()
            cl_norm = re.sub(r'[^a-z0-9]', '', clean_name.lower())
            if cl_norm == cand_norm or (len(cl_norm) > 3 and cl_norm in cand_norm) or (len(cand_norm) > 3 and cand_norm in cl_norm):
                return dict(cl), candidate_name

            ratio = difflib.SequenceMatcher(None, cand_norm, cl_norm).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = cl

        if best_ratio >= 0.70 and best_match:
            return dict(best_match), candidate_name

        if create_if_missing and len(candidate_name.split()) <= 4 and len(cand_norm) >= 3:
            clean_formatted_name = candidate_name.title()
            email_part = re.sub(r'[^a-z0-9]', '', clean_formatted_name.lower())
            cur = conn.execute(
                "INSERT INTO clients (name, phone, email) VALUES (?, ?, ?)",
                (clean_formatted_name, "+91 98000 00000", f"{email_part}@example.com")
            )
            conn.commit()
            return {"id": cur.lastrowid, "name": clean_formatted_name}, candidate_name

    for cl in clients:
        clean_name = re.sub(r'\(.*?\)', '', cl["name"]).strip()
        tokens = [tk.lower() for tk in re.split(r'\s+', clean_name) if len(tk) > 2]
        if any(tk in t_lower.split() for tk in tokens):
            return dict(cl), candidate_name

    return (dict(clients[0]) if clients else None), candidate_name


def extract_amount_and_desc(transcript: str, client_name: str, candidate_name: Optional[str] = None):
    cleaned = re.sub(r'(\d+),(\d+)', r'\1\2', transcript)
    amount = 5000.0

    m_k = re.search(r'(\d+(?:\.\d+)?)\s*(?:k|thousand)\b', cleaned, flags=re.I)
    if m_k:
        amount = float(m_k.group(1)) * 1000
    else:
        m_l = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac)\b', cleaned, flags=re.I)
        if m_l:
            amount = float(m_l.group(1)) * 100000
        else:
            nums = re.findall(r'\b\d+(?:\.\d{1,2})?\b', cleaned)
            for n in nums:
                val = float(n)
                if val >= 50:
                    amount = val
                    break

    t = transcript
    t = re.sub(r'^(?:please\s+)?(?:can\s+you\s+)?(?:create|make|generate|add|issue|bill|record)\s+(?:an?\s+)?(?:invoice|bill|payment)?\s*(?:for\s+)?', '', t, flags=re.I)

    names_to_remove = [client_name]
    if candidate_name:
        names_to_remove.append(candidate_name)

    for n in names_to_remove:
        clean_n = re.sub(r'\(.*?\)', '', n).strip()
        t = re.sub(re.escape(clean_n), '', t, flags=re.I)
        for w in re.findall(r'[A-Za-z]+', clean_n):
            if len(w) > 1:
                t = re.sub(r'\b' + re.escape(w) + r'\b', '', t, flags=re.I)

    t = re.sub(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', '', t)
    t = re.sub(r'\b(rupees|rs\.?|inr|of|amount|worth|only|a|an|the|towards|please|bill|thousand|lakh|lac|k)\b', '', t, flags=re.I)
    t = re.sub(r'^\s*for\s+', '', t, flags=re.I)

    desc = ' '.join(t.split()).strip(' -:,')
    desc = desc.capitalize() if desc and len(desc) >= 3 else 'Voice Assistant Order'
    return amount, desc


@app.get("/api/voice-commands")
def list_voice_commands():
    """Returns recent voice assistant command logs and intent classifications."""
    with get_connection() as c:
        rows = c.execute("SELECT * FROM voice_commands ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


@app.post("/api/voice-commands", status_code=status.HTTP_201_CREATED)
def log_voice_command(body: VoiceCommandCreate):
    """Processes spoken or typed command, logs intent, and executes corresponding business action."""
    transcript = body.transcript.strip()
    intent = (body.intent or classify_voice_command(transcript)).strip()
    action_taken = None
    created_invoice = None

    with get_connection() as c:
        cur = c.execute(
            "INSERT INTO voice_commands (transcript, intent) VALUES (?, ?)",
            (transcript, intent)
        )
        log_id = cur.lastrowid
        c.commit()

        t = transcript.lower()

        # Action: Create invoice
        if intent == "CREATE_INVOICE" or ("invoice" in t and any(w in t for w in ["create", "make", "generate", "bill", "issue"])):
            matched_client, candidate_name = resolve_client_from_transcript(transcript, c, create_if_missing=True)
            if matched_client:
                amount, desc = extract_amount_and_desc(transcript, matched_client["name"], candidate_name)
                due_date = str(date.today())
                cur_inv = c.execute("""
                    INSERT INTO invoices (client_id, description, amount, due_date, upi_id, status)
                    VALUES (?, ?, ?, ?, 'chatbiz.merchant@upi', 'Pending')
                """, (matched_client["id"], desc, amount, due_date))
                new_inv_id = cur_inv.lastrowid
                seed_invoice_reminders(new_inv_id, due_date)
                c.commit()

                action_taken = f"Invoice #INV-{new_inv_id:04d} created for {matched_client['name']} (Rs. {amount:,.2f}) — '{desc}'"
                row = c.execute("SELECT i.*, c.name AS client_name FROM invoices i JOIN clients c ON i.client_id=c.id WHERE i.id=?", (new_inv_id,)).fetchone()
                created_invoice = dict(row)

        # Action: Record payment
        elif intent == "RECORD_PAYMENT" or ("payment" in t and any(w in t for w in ["record", "received", "paid", "mark"])):
            matched_client, _ = resolve_client_from_transcript(transcript, c, create_if_missing=False)
            query = "SELECT id, amount, client_id FROM invoices WHERE status!='Paid'"
            params = []
            if matched_client:
                query += " AND client_id=?"
                params.append(matched_client["id"])
            query += " ORDER BY id DESC LIMIT 1"
            target_inv = c.execute(query, params).fetchone()
            if target_inv:
                c.execute("UPDATE invoices SET status='Paid' WHERE id=?", (target_inv["id"],))
                tx_id = f"VOICE/{datetime.now().strftime('%Y%m%d%H%M%S')}"
                c.execute("""
                    INSERT INTO payments (invoice_id, amount, transaction_id, payment_date, source, raw_text)
                    VALUES (?, ?, ?, ?, 'voice', ?)
                """, (target_inv["id"], target_inv["amount"], tx_id, str(date.today()), f"Voice: {transcript}"))
                c.commit()
                action_taken = f"Invoice #INV-{target_inv['id']:04d} marked as Paid (Rs. {target_inv['amount']:,.2f})"

        # Action: Send reminder
        elif intent == "SEND_REMINDER" or "reminder" in t:
            rem = c.execute("SELECT id, invoice_id FROM reminders WHERE status='PENDING' ORDER BY id DESC LIMIT 1").fetchone()
            if rem:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("UPDATE reminders SET status='SENT', sent_at=? WHERE id=?", (now_str, rem["id"]))
                c.commit()
                action_taken = f"WhatsApp reminder for Invoice #{rem['invoice_id']} sent!"

        new_log = c.execute("SELECT * FROM voice_commands WHERE id=?", (log_id,)).fetchone()
        return {
            "message": "Voice command processed successfully",
            "command": dict(new_log),
            "action_taken": action_taken,
            "invoice": created_invoice
        }


@app.post("/api/voice/demo")
def voice_demo(body: VoiceDemo):
    """Demo endpoint for voice pipeline without WhatsApp permissions."""
    transcript = transcribe_demo(body.transcript)
    intent = classify_voice_command(transcript)
    with get_connection() as conn:
        conn.execute("INSERT INTO voice_commands(transcript, intent) VALUES (?, ?)", (transcript, intent))
        conn.commit()
    return {
        "transcript": transcript,
        "intent": intent,
        "message": "Voice pipeline demonstrated without WhatsApp permissions."
    }


# ---------------------------------------------------------
# Database Seed & CSV Export Endpoints (Sprint 6)
# ---------------------------------------------------------
@app.post("/api/db/seed")
def seed_database(force: bool = False):
    """Seeds sample data into the database. Pass force=True to reset all tables."""
    with get_connection() as conn:
        result = seed_sample_data(conn, force=force)
        return result


@app.get("/api/export/invoices")
def export_invoices():
    """Streams CSV download of all invoice records."""
    with get_connection() as c:
        rows = c.execute("""
            SELECT i.id, c.name AS client_name, i.description, i.amount, i.due_date, i.status, i.upi_id
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            ORDER BY i.id ASC
        """).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Invoice ID", "Client Name", "Description", "Amount (INR)", "Due Date", "Status", "UPI ID"])
    writer.writerows([tuple(r) for r in rows])
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=chatbiz_invoices.csv"}
    )


# ---------------------------------------------------------
# WhatsApp Business AI Chat Endpoints (Client & Manager)
# ---------------------------------------------------------
@app.get("/api/chat/history")
def fetch_chat_history(
    session_id: Optional[str] = Query(None),
    client_id: Optional[int] = Query(None)
):
    """
    Returns WhatsApp chat messages for a specific client session or manager session.
    If empty, initializes with a personalized welcome message.
    """
    with get_connection() as conn:
        resolved_session = session_id
        if not resolved_session and client_id:
            resolved_session = f"client_{client_id}"
        elif not resolved_session:
            resolved_session = "manager"

        history = get_chat_history(conn, resolved_session)

        # If history is empty, populate an initial greeting
        if not history:
            if client_id:
                client = conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
                c_name = client["name"] if client else "Valued Client"
                fname = c_name.split()[0]
                pending = conn.execute(
                    "SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE client_id=? AND status!='Paid'",
                    (client_id,)
                ).fetchone()[0]
                bal_text = f"Your current outstanding balance is ₹{pending:,.2f}." if pending > 0 else "Your account has zero outstanding balance."
                welcome_msg = (
                    f"Hello {fname}! 👋 Welcome to ChatBiz Automated WhatsApp Business.\n\n"
                    f"{bal_text}\n\n"
                    f"I can assist you with your balance, invoice PDFs, UPI payment QR codes, and payment history in natural language. How may I help you today?"
                )
                save_chat_message(
                    conn=conn,
                    session_id=resolved_session,
                    role="assistant",
                    sender="ChatBiz AI (WhatsApp Business)",
                    content=welcome_msg,
                    client_id=client_id,
                    metadata={"type": "welcome", "pending_balance": pending}
                )
            else:
                welcome_msg = (
                    "Hello Manager! 👔 Welcome to your ChatBiz WhatsApp Operations Assistant.\n\n"
                    "I can execute natural language operations for you:\n"
                    "• *'Show details for client Rajesh Patel'*\n"
                    "• *'Create invoice for Rohit 5000 due 2026-11-15'*\n"
                    "• *'What is our total revenue & collection rate?'*\n"
                    "• *'List all overdue invoices'*\n"
                    "• *'Mark invoice 2 as paid'*\n\n"
                    "Type any command or query to get started!"
                )
                save_chat_message(
                    conn=conn,
                    session_id=resolved_session,
                    role="assistant",
                    sender="ChatBiz Operations AI",
                    content=welcome_msg,
                    client_id=None,
                    metadata={"type": "welcome"}
                )
            history = get_chat_history(conn, resolved_session)

        return {"session_id": resolved_session, "messages": history}


@app.post("/api/chat/client")
def send_client_chat(payload: ClientChatRequest):
    """
    Processes natural language message from a selected client, answering regarding
    invoices, dues, payment UPI, and business queries.
    """
    with get_connection() as conn:
        result = handle_client_message(
            client_id=payload.client_id,
            message=payload.message,
            conn=conn
        )
        return result


@app.post("/api/chat/manager")
def send_manager_chat(payload: ManagerChatRequest):
    """
    Processes natural language command from manager, executing client dossier lookups,
    invoice issuance, payment settlements, reminders, and financial KPI analytics.
    """
    with get_connection() as conn:
        result = handle_manager_message(
            message=payload.message,
            conn=conn
        )
        return result


@app.post("/api/chat/clear")
def clear_chat(payload: ClearChatRequest):
    """Clears conversation messages for a client session or manager thread."""
    with get_connection() as conn:
        target_session = payload.session_id
        if not target_session and payload.client_id:
            target_session = f"client_{payload.client_id}"
        elif not target_session:
            target_session = "manager"

        cleared_count = clear_chat_history(conn, target_session)
        return {"message": f"Cleared {cleared_count} messages for session {target_session}."}

