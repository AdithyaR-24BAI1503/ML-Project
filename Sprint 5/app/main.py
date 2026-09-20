from fastapi import FastAPI
from pydantic import BaseModel
from .database import init_db, get_connection
from .reminders import seed_invoice_reminders, run_due_reminders
from .voice import transcribe_demo, classify_voice_command

app = FastAPI(title="ChatBiz — Sprint 5", version="5.0")

class VoiceDemo(BaseModel):
    transcript: str

class RecurringInvoice(BaseModel):
    client_id: int
    description: str
    amount: float
    due_date: str
    recurrence: str = "MONTHLY"

@app.on_event("startup")
def startup():
    init_db()

@app.post("/api/reminders/seed/{invoice_id}")
def seed(invoice_id: int, due_date: str):
    seed_invoice_reminders(invoice_id, due_date)
    return {"message": "Reminder schedule created.", "invoice_id": invoice_id}

@app.post("/api/reminders/run")
def run_reminders():
    return {"sent": run_due_reminders()}

@app.get("/api/reminders")
def reminders():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM reminders ORDER BY id DESC").fetchall()]

@app.post("/api/voice/demo")
def voice_demo(body: VoiceDemo):
    transcript = transcribe_demo(body.transcript)
    intent = classify_voice_command(transcript)
    with get_connection() as conn:
        conn.execute("INSERT INTO voice_commands(transcript,intent) VALUES (?,?)",
                     (transcript, intent))
        conn.commit()
    return {"transcript": transcript, "intent": intent,
            "message": "Voice pipeline demonstrated without WhatsApp permissions."}

@app.post("/api/recurring-invoices")
def recurring(body: RecurringInvoice):
    with get_connection() as conn:
        cur = conn.execute('''
            INSERT INTO invoices(client_id,description,amount,due_date,recurring,recurrence)
            VALUES (?,?,?,?,1,?)''',
            (body.client_id, body.description, body.amount, body.due_date, body.recurrence))
        conn.commit()
    seed_invoice_reminders(cur.lastrowid, body.due_date)
    return {"invoice_id": cur.lastrowid, "recurrence": body.recurrence, "message": "Recurring invoice created."}
