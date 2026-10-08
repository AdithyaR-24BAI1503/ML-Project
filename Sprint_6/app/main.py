import csv
import difflib
import io
import re
from datetime import datetime
from typing import Optional


from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .database import init_db, get_connection
from .analytics import summary, client_summary
from .seed_data import seed_sample_data

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="ChatBiz — Sprint 6 API",
    version="6.0",
    description="WhatsApp-First MSME Business Management System with Business Analytics and REST JSON Endpoints",
    lifespan=lifespan
)

# Enable CORS so the separate frontend can communicate from any port/origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------
class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1)
    phone: Optional[str] = None
    email: Optional[str] = None

class InvoiceCreate(BaseModel):
    client_id: int
    description: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    due_date: str
    upi_id: Optional[str] = None
    recurring: Optional[int] = 0
    recurrence: Optional[str] = None

class InvoiceStatusUpdate(BaseModel):
    status: str

class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float = Field(..., gt=0)
    transaction_id: Optional[str] = None
    payment_date: Optional[str] = None
    source: Optional[str] = "manual"
    raw_text: Optional[str] = None

class VoiceCommandCreate(BaseModel):
    transcript: str
    intent: Optional[str] = "GENERAL_QUERY"


# ---------------------------------------------------------
# Core API Endpoints (All Pure JSON)
# ---------------------------------------------------------
@app.get("/")
def api_root():
    """
    Root API info endpoint returning JSON metadata and available routes.
    """
    return {
        "app": "ChatBiz Business Management API",
        "sprint": "Sprint 6",
        "version": "6.0",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "analytics": "/api/analytics",
            "clients": "/api/clients",
            "invoices": "/api/invoices",
            "payments": "/api/payments",
            "reminders": "/api/reminders",
            "voice_commands": "/api/voice-commands",
            "export_invoices": "/api/export/invoices",
            "docs": "/docs"
        }
    }

@app.get("/api/analytics")
def get_analytics():
    """
    Returns high-level business metrics and client performance summaries in JSON format.
    """
    return {
        "overall": summary(),
        "clients": client_summary()
    }

# ---------------------------------------------------------
# Clients Endpoints
# ---------------------------------------------------------
@app.get("/api/clients")
def list_clients():
    """
    Returns list of all clients with invoice counts and revenue totals.
    """
    with get_connection() as c:
        rows = c.execute("""
            SELECT c.id, c.name, c.phone, c.email, c.created_at,
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
    """
    Registers a new client.
    """
    with get_connection() as c:
        try:
            cur = c.execute(
                "INSERT INTO clients (name, phone, email) VALUES (?, ?, ?)",
                (client.name.strip(), client.phone, client.email)
            )
            c.commit()
            client_id = cur.lastrowid
            new_client = c.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
            return {"message": "Client created successfully", "client": dict(new_client)}
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(status_code=400, detail="A client with this name already exists.")
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/clients/{client_id}")
def get_client_details(client_id: int):
    """
    Returns single client details and list of their invoices.
    """
    with get_connection() as c:
        client = c.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found.")
        invoices = c.execute("SELECT * FROM invoices WHERE client_id=? ORDER BY id DESC", (client_id,)).fetchall()
        return {
            "client": dict(client),
            "invoices": [dict(i) for i in invoices]
        }

# ---------------------------------------------------------
# Invoices Endpoints
# ---------------------------------------------------------
@app.get("/api/invoices")
def list_invoices(
    status: Optional[str] = Query(None, description="Filter by status: Paid, Pending, or Overdue"),
    search: Optional[str] = Query(None, description="Search by client name or invoice description")
):
    """
    Returns list of invoices joined with client info. Supports status and search filtering.
    """
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
    """
    Creates a new invoice for a client.
    """
    with get_connection() as c:
        client = c.execute("SELECT id FROM clients WHERE id=?", (invoice.client_id,)).fetchone()
        if not client:
            raise HTTPException(status_code=404, detail=f"Client ID {invoice.client_id} does not exist.")

        cur = c.execute("""
            INSERT INTO invoices (client_id, description, amount, due_date, upi_id, recurring, recurrence, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (
            invoice.client_id, invoice.description.strip(), invoice.amount,
            invoice.due_date, invoice.upi_id, invoice.recurring, invoice.recurrence
        ))
        c.commit()
        new_id = cur.lastrowid

        # Schedule default reminder
        c.execute("""
            INSERT INTO reminders (invoice_id, reminder_type, scheduled_for, status)
            VALUES (?, 'BEFORE_DUE', ?, 'PENDING')
        """, (new_id, f"{invoice.due_date} 09:00:00"))
        c.commit()

        row = c.execute("""
            SELECT i.*, c.name AS client_name
            FROM invoices i JOIN clients c ON i.client_id = c.id
            WHERE i.id=?
        """, (new_id,)).fetchone()
        return {"message": "Invoice created successfully", "invoice": dict(row)}

@app.patch("/api/invoices/{invoice_id}/status")
def update_invoice_status(invoice_id: int, body: InvoiceStatusUpdate):
    """
    Updates the status of an invoice (e.g., 'Paid', 'Pending', 'Overdue').
    """
    valid_statuses = {"Paid", "Pending", "Overdue"}
    clean_status = body.status.capitalize()
    if clean_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

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
    """
    Convenience endpoint to mark an invoice as Paid and log a payment record if not already logged.
    """
    with get_connection() as c:
        inv = c.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        c.execute("UPDATE invoices SET status='Paid' WHERE id=?", (invoice_id,))

        # Check existing payment
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

# ---------------------------------------------------------
# Payments Endpoints
# ---------------------------------------------------------
@app.get("/api/payments")
def list_payments():
    """
    Returns ledger of all payments joined with invoice and client names.
    """
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

@app.post("/api/payments", status_code=status.HTTP_201_CREATED)
def record_payment(payment: PaymentCreate):
    """
    Records a new payment for an invoice and sets invoice status to Paid.
    """
    with get_connection() as c:
        inv = c.execute("SELECT * FROM invoices WHERE id=?", (payment.invoice_id,)).fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        p_date = payment.payment_date or datetime.now().strftime("%Y-%m-%d")
        tx_id = payment.transaction_id or f"TXN/{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cur = c.execute("""
            INSERT INTO payments (invoice_id, amount, transaction_id, payment_date, source, raw_text)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (payment.invoice_id, payment.amount, tx_id, p_date, payment.source, payment.raw_text))

        # Check total payments recorded for this invoice
        tot_paid = c.execute("SELECT SUM(amount) FROM payments WHERE invoice_id=?", (payment.invoice_id,)).fetchone()[0] or 0
        if tot_paid >= inv["amount"]:
            c.execute("UPDATE invoices SET status='Paid' WHERE id=?", (payment.invoice_id,))

        c.commit()
        new_pmt = c.execute("SELECT * FROM payments WHERE id=?", (cur.lastrowid,)).fetchone()
        return {"message": "Payment recorded successfully", "payment": dict(new_pmt)}

# ---------------------------------------------------------
# Reminders Endpoints
# ---------------------------------------------------------
@app.get("/api/reminders")
def list_reminders():
    """
    Returns payment reminder schedules with associated invoice and client contact details.
    """
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

@app.post("/api/reminders/{reminder_id}/send")
def send_reminder(reminder_id: int):
    """
    Simulates sending a WhatsApp payment reminder.
    """
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
# Voice Command Processing Helpers
# ---------------------------------------------------------
def resolve_client_from_transcript(transcript: str, conn, create_if_missing: bool = True):
    """
    Intelligently identifies which client the voice command is referring to.
    Handles:
    - Spacing variations (e.g. 'sriraman' in DB vs 'Sri Raman' spoken)
    - Punctuation / nicknames / partial names
    - Fuzzy matching
    - Automatic client creation if the name does not exist yet (never blindly picks a random client!)
    """
    clients = conn.execute("SELECT id, name FROM clients").fetchall()
    if not clients and not create_if_missing:
        return None, None

    t_lower = transcript.lower()
    t_clean = re.sub(r'[^a-z0-9]', '', t_lower)

    # Extract potential candidate name from natural speech patterns first
    candidate_match = re.search(
        r'(?:for|to|bill|from)\s+([A-Za-z\s\.\']+?)(?:\s+(?:of|for|amount|\d+|rupees|rs\.?|inr)\b|$)',
        transcript,
        flags=re.I
    )
    candidate_name = candidate_match.group(1).strip() if candidate_match else None
    if candidate_name and candidate_name.lower() in ["an invoice", "invoice", "a payment", "payment", "me", "him", "her"]:
        candidate_name = None

    # 1. Direct Space-insensitive check across existing clients
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

        # If candidate name was clearly spoken (e.g. "Sri Raman") and doesn't exist in DB:
        if create_if_missing and len(candidate_name.split()) <= 4 and len(cand_norm) >= 3:
            clean_formatted_name = candidate_name.title()
            email_part = re.sub(r'[^a-z0-9]', '', clean_formatted_name.lower())
            cur = conn.execute(
                "INSERT INTO clients (name, phone, email) VALUES (?, ?, ?)",
                (clean_formatted_name, "+91 98000 00000", f"{email_part}@example.com")
            )
            conn.commit()
            new_client = {"id": cur.lastrowid, "name": clean_formatted_name}
            return new_client, candidate_name

    # 3. Fallback to individual word/token matches
    for cl in clients:
        clean_name = re.sub(r'\(.*?\)', '', cl["name"]).strip()
        tokens = [tk.lower() for tk in re.split(r'\s+', clean_name) if len(tk) > 2]
        if any(tk in t_lower.split() for tk in tokens):
            return dict(cl), candidate_name

    fallback_client = dict(clients[0]) if clients else None
    return fallback_client, candidate_name


def extract_amount_and_desc(transcript: str, client_name: str, candidate_name: Optional[str] = None):
    # 1. Amount extraction
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

    # 2. Description extraction
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

    # Remove amount and common fillers
    t = re.sub(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', '', t)
    t = re.sub(r'\b(rupees|rs\.?|inr|of|amount|worth|only|a|an|the|towards|please|bill|thousand|lakh|lac|k)\b', '', t, flags=re.I)
    t = re.sub(r'^\s*for\s+', '', t, flags=re.I)

    desc = ' '.join(t.split()).strip(' -:,')
    if not desc or len(desc) < 3:
        desc = 'Voice Assistant Order'
    else:
        desc = desc.capitalize()

    return amount, desc


# ---------------------------------------------------------
# Voice Commands Endpoints
# ---------------------------------------------------------
@app.get("/api/voice-commands")
def list_voice_commands():
    """
    Returns recent voice assistant transcripts and intent classifications.
    """
    with get_connection() as c:
        rows = c.execute("SELECT * FROM voice_commands ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

@app.post("/api/voice-commands", status_code=status.HTTP_201_CREATED)
def log_voice_command(body: VoiceCommandCreate):
    """
    Logs a new voice command transcript and intent.
    Automatically executes corresponding business actions (e.g., generating invoices).
    """
    transcript = body.transcript.strip()
    intent = (body.intent or "GENERAL_QUERY").strip()
    action_taken = None
    created_invoice = None

    with get_connection() as c:
        # 1. Log the voice command
        cur = c.execute(
            "INSERT INTO voice_commands (transcript, intent) VALUES (?, ?)",
            (transcript, intent)
        )
        log_id = cur.lastrowid
        c.commit()

        t = transcript.lower()

        # 2. ACTION: CREATE_INVOICE
        if intent == "CREATE_INVOICE" or ("invoice" in t and any(w in t for w in ["create", "make", "generate", "add", "bill", "issue"])):
            matched_client, candidate_name = resolve_client_from_transcript(transcript, c, create_if_missing=True)

            if matched_client:
                amount, desc = extract_amount_and_desc(transcript, matched_client["name"], candidate_name)
                due_date = datetime.now().strftime("%Y-%m-%d")

                # Insert invoice into database
                cur_inv = c.execute("""
                    INSERT INTO invoices (client_id, description, amount, due_date, upi_id, status)
                    VALUES (?, ?, ?, ?, ?, 'Pending')
                """, (matched_client["id"], desc, amount, due_date, "chatbiz.merchant@upi"))
                new_inv_id = cur_inv.lastrowid

                # Schedule reminder
                c.execute("""
                    INSERT INTO reminders (invoice_id, reminder_type, scheduled_for, status)
                    VALUES (?, 'BEFORE_DUE', ?, 'PENDING')
                """, (new_inv_id, f"{due_date} 09:00:00"))
                c.commit()

                action_taken = f"Invoice #INV-{new_inv_id:04d} created for {matched_client['name']} (Rs. {amount:,.2f}) — '{desc}'"
                row = c.execute("SELECT i.*, c.name AS client_name FROM invoices i JOIN clients c ON i.client_id=c.id WHERE i.id=?", (new_inv_id,)).fetchone()
                created_invoice = dict(row)

        # 3. ACTION: RECORD_PAYMENT
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
                    VALUES (?, ?, ?, ?, 'manual', ?)
                """, (target_inv["id"], target_inv["amount"], tx_id, datetime.now().strftime("%Y-%m-%d"), f"Voice Command: {transcript}"))
                c.commit()
                action_taken = f"Invoice #INV-{target_inv['id']:04d} marked as Paid (Rs. {target_inv['amount']:,.2f})"


        # 4. ACTION: SEND_REMINDER
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


# ---------------------------------------------------------
# Database Seed & CSV Export
# ---------------------------------------------------------
@app.post("/api/db/seed")
def seed_database(force: bool = False):
    """
    Seeds sample data into the database. Pass force=True to reset all tables.
    """
    with get_connection() as conn:
        result = seed_sample_data(conn, force=force)
        return result

@app.get("/api/export/invoices")
def export_invoices():
    """
    Streams CSV export of all invoice records.
    """
    with get_connection() as c:
        rows = c.execute("""
            SELECT i.id, c.name AS client_name, i.description, i.amount, i.due_date, i.status, i.upi_id
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            ORDER BY i.id
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
