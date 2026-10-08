"""
ChatBiz Sample Data Seeder
Populates realistic Indian MSME business profiles, invoices, payments,
reminders, and voice command logs for demonstrations and frontend display.
"""

SAMPLE_CLIENTS = [
    {
        "name": "Ramesh Kumar (Kirana Store)",
        "phone": "+91 98765 43210",
        "email": "ramesh.kirana@example.com"
    },
    {
        "name": "Priya Sharma (Home Bakery)",
        "phone": "+91 98234 56789",
        "email": "priya.bakes@example.com"
    },
    {
        "name": "Amit Patel (Web Developer)",
        "phone": "+91 97123 45678",
        "email": "amit.code@example.com"
    },
    {
        "name": "Ananya Rao (Math & Science Tutor)",
        "phone": "+91 96543 21098",
        "email": "ananya.tutoring@example.com"
    },
    {
        "name": "Rajesh Singh (Tempo Logistics)",
        "phone": "+91 95432 10987",
        "email": "rajesh.transport@example.com"
    },
    {
        "name": "Sunita Verma (Handicrafts & Boutique)",
        "phone": "+91 94321 09876",
        "email": "sunita.boutique@example.com"
    },
    {
        "name": "Vikram Malhotra (Digital Media Agency)",
        "phone": "+91 93210 98765",
        "email": "vikram.media@example.com"
    },
    {
        "name": "Deepak Mehta (Wholesale Electricals)",
        "phone": "+91 92109 87654",
        "email": "deepak.electric@example.com"
    }
]

# client_idx is 1-based index corresponding to SAMPLE_CLIENTS
SAMPLE_INVOICES = [
    {
        "client_idx": 1,
        "description": "Monthly Grocery Inventory Batch #401",
        "amount": 18500.0,
        "due_date": "2026-09-15",
        "upi_id": "ramesh.kirana@upi",
        "status": "Paid",
        "recurring": 1,
        "recurrence": "MONTHLY",
        "created_at": "2026-09-01 10:30:00"
    },
    {
        "client_idx": 1,
        "description": "Wholesale Grains & Pulses Delivery",
        "amount": 9200.0,
        "due_date": "2026-09-25",
        "upi_id": "ramesh.kirana@upi",
        "status": "Pending",
        "recurring": 0,
        "recurrence": None,
        "created_at": "2026-09-16 11:15:00"
    },
    {
        "client_idx": 2,
        "description": "Custom 3-Tier Anniversary Fondant Cake",
        "amount": 4500.0,
        "due_date": "2026-09-10",
        "upi_id": "priya.bakes@okhdfcbank",
        "status": "Paid",
        "recurring": 0,
        "recurrence": None,
        "created_at": "2026-09-05 14:20:00"
    },
    {
        "client_idx": 2,
        "description": "Corporate Party Dessert Catering (50 boxes)",
        "amount": 12000.0,
        "due_date": "2026-09-18",
        "upi_id": "priya.bakes@okhdfcbank",
        "status": "Overdue",
        "recurring": 0,
        "recurrence": None,
        "created_at": "2026-09-08 09:45:00"
    },
    {
        "client_idx": 3,
        "description": "E-Commerce Website Redesign - Milestone 1",
        "amount": 25000.0,
        "due_date": "2026-09-05",
        "upi_id": "amit.patel@okaxis",
        "status": "Paid",
        "recurring": 0,
        "recurrence": None,
        "created_at": "2026-08-25 16:00:00"
    },
    {
        "client_idx": 3,
        "description": "FastAPI Backend & UPI QR Integration",
        "amount": 15000.0,
        "due_date": "2026-09-28",
        "upi_id": "amit.patel@okaxis",
        "status": "Pending",
        "recurring": 0,
        "recurrence": None,
        "created_at": "2026-09-14 12:10:00"
    },
    {
        "client_idx": 4,
        "description": "Grade 10 Board Exam Prep - September Tuition",
        "amount": 6000.0,
        "due_date": "2026-09-07",
        "upi_id": "ananya.math@oksbi",
        "status": "Paid",
        "recurring": 1,
        "recurrence": "MONTHLY",
        "created_at": "2026-09-01 08:30:00"
    },
    {
        "client_idx": 4,
        "description": "Special Advanced Physics Coaching Package",
        "amount": 3500.0,
        "due_date": "2026-09-22",
        "upi_id": "ananya.math@oksbi",
        "status": "Pending",
        "recurring": 0,
        "recurrence": None,
        "created_at": "2026-09-15 17:40:00"
    },
    {
        "client_idx": 5,
        "description": "Intercity Goods Transport - 2 Trips (Chennai to Salem)",
        "amount": 14000.0,
        "due_date": "2026-09-12",
        "upi_id": "rajesh.transport@upi",
        "status": "Overdue",
        "recurring": 0,
        "recurrence": None,
        "created_at": "2026-09-02 11:00:00"
    },
    {
        "client_idx": 5,
        "description": "Local Tempo Delivery Service - Weekly Retainer",
        "amount": 7500.0,
        "due_date": "2026-09-30",
        "upi_id": "rajesh.transport@upi",
        "status": "Pending",
        "recurring": 1,
        "recurrence": "WEEKLY",
        "created_at": "2026-09-18 10:00:00"
    },
    {
        "client_idx": 6,
        "description": "Handcrafted Silk Sarees & Ethnic Stoles Order",
        "amount": 16500.0,
        "due_date": "2026-09-14",
        "upi_id": "sunita.boutique@icici",
        "status": "Paid",
        "recurring": 0,
        "recurrence": None,
        "created_at": "2026-09-04 15:30:00"
    },
    {
        "client_idx": 6,
        "description": "Festive Exhibition Stall Sample Garments",
        "amount": 8200.0,
        "due_date": "2026-09-27",
        "upi_id": "sunita.boutique@icici",
        "status": "Pending",
        "recurring": 0,
        "recurrence": None,
        "created_at": "2026-09-17 14:15:00"
    },
    {
        "client_idx": 7,
        "description": "Monthly SEO & Instagram Marketing Retainer",
        "amount": 22000.0,
        "due_date": "2026-09-05",
        "upi_id": "vikram.agency@kotak",
        "status": "Paid",
        "recurring": 1,
        "recurrence": "MONTHLY",
        "created_at": "2026-09-01 09:00:00"
    },
    {
        "client_idx": 7,
        "description": "Google Ads Campaign Setup & Creative Assets",
        "amount": 11500.0,
        "due_date": "2026-09-19",
        "upi_id": "vikram.agency@kotak",
        "status": "Overdue",
        "recurring": 0,
        "recurrence": None,
        "created_at": "2026-09-06 13:20:00"
    },
    {
        "client_idx": 8,
        "description": "Copper Wires & MCB Distribution Batch #88",
        "amount": 34000.0,
        "due_date": "2026-09-16",
        "upi_id": "deepak.electric@barodampay",
        "status": "Paid",
        "recurring": 0,
        "recurrence": None,
        "created_at": "2026-09-02 10:45:00"
    },
    {
        "client_idx": 8,
        "description": "Commercial LED Panels & Switches Supply",
        "amount": 19500.0,
        "due_date": "2026-09-29",
        "upi_id": "deepak.electric@barodampay",
        "status": "Pending",
        "recurring": 0,
        "recurrence": None,
        "created_at": "2026-09-18 16:30:00"
    }
]

# invoice_idx corresponds to 1-based index in SAMPLE_INVOICES
SAMPLE_PAYMENTS = [
    {
        "invoice_idx": 1,
        "amount": 18500.0,
        "transaction_id": "UPI/20260914/AXIS/882194721",
        "payment_date": "2026-09-14",
        "source": "upi_webhook",
        "raw_text": "Paid Rs. 18,500 via Google Pay to Ramesh Kirana. Ref 882194721."
    },
    {
        "invoice_idx": 3,
        "amount": 4500.0,
        "transaction_id": "UPI/20260909/HDFC/319847120",
        "payment_date": "2026-09-09",
        "source": "ocr",
        "raw_text": "Payment Successful. Rs. 4,500 sent to Priya Bakery on Sep 9, 2026."
    },
    {
        "invoice_idx": 5,
        "amount": 25000.0,
        "transaction_id": "NEFT/20260904/SBIN/551928471",
        "payment_date": "2026-09-04",
        "source": "manual",
        "raw_text": "Recorded from bank statement credit alert."
    },
    {
        "invoice_idx": 7,
        "amount": 6000.0,
        "transaction_id": "UPI/20260906/PAYTM/774619283",
        "payment_date": "2026-09-06",
        "source": "upi_webhook",
        "raw_text": "PhonePe payment of Rs 6,000 received for Ananya Math Tuition."
    },
    {
        "invoice_idx": 11,
        "amount": 16500.0,
        "transaction_id": "UPI/20260913/ICIC/118274639",
        "payment_date": "2026-09-13",
        "source": "ocr",
        "raw_text": "Transferred Rs. 16,500 to Sunita Boutique via Paytm UPI."
    },
    {
        "invoice_idx": 13,
        "amount": 22000.0,
        "transaction_id": "IMPS/20260905/KKBK/993817264",
        "payment_date": "2026-09-05",
        "source": "manual",
        "raw_text": "Client confirmed IMPS payment receipt on WhatsApp."
    },
    {
        "invoice_idx": 15,
        "amount": 34000.0,
        "transaction_id": "RTGS/20260915/BARB/440192837",
        "payment_date": "2026-09-15",
        "source": "manual",
        "raw_text": "Direct NEFT/RTGS settlement from Deepak Wholesale."
    }
]

SAMPLE_REMINDERS = [
    {
        "invoice_idx": 2,
        "reminder_type": "BEFORE_DUE",
        "scheduled_for": "2026-09-23 09:00:00",
        "status": "PENDING",
        "sent_at": None
    },
    {
        "invoice_idx": 4,
        "reminder_type": "OVERDUE",
        "scheduled_for": "2026-09-19 10:00:00",
        "status": "SENT",
        "sent_at": "2026-09-19 10:02:15"
    },
    {
        "invoice_idx": 4,
        "reminder_type": "OVERDUE",
        "scheduled_for": "2026-09-21 11:30:00",
        "status": "SENT",
        "sent_at": "2026-09-21 11:31:40"
    },
    {
        "invoice_idx": 6,
        "reminder_type": "BEFORE_DUE",
        "scheduled_for": "2026-09-26 09:30:00",
        "status": "PENDING",
        "sent_at": None
    },
    {
        "invoice_idx": 8,
        "reminder_type": "DUE_TODAY",
        "scheduled_for": "2026-09-22 08:00:00",
        "status": "PENDING",
        "sent_at": None
    },
    {
        "invoice_idx": 9,
        "reminder_type": "OVERDUE",
        "scheduled_for": "2026-09-13 10:00:00",
        "status": "SENT",
        "sent_at": "2026-09-13 10:01:22"
    },
    {
        "invoice_idx": 9,
        "reminder_type": "OVERDUE",
        "scheduled_for": "2026-09-18 10:00:00",
        "status": "SENT",
        "sent_at": "2026-09-18 10:05:08"
    },
    {
        "invoice_idx": 14,
        "reminder_type": "OVERDUE",
        "scheduled_for": "2026-09-20 09:30:00",
        "status": "SENT",
        "sent_at": "2026-09-20 09:32:05"
    }
]

SAMPLE_VOICE_COMMANDS = [
    {
        "transcript": "Create invoice for Ramesh Kumar 9200 rupees for wholesale pulses",
        "intent": "CREATE_INVOICE"
    },
    {
        "transcript": "Check all overdue payments for this month",
        "intent": "VIEW_OVERDUE"
    },
    {
        "transcript": "Send urgent payment reminder to Rajesh Singh for tempo logistics",
        "intent": "SEND_REMINDER"
    },
    {
        "transcript": "Record payment of 4500 rupees received from Priya Bakery",
        "intent": "RECORD_PAYMENT"
    },
    {
        "transcript": "Show me total business revenue and client summary",
        "intent": "VIEW_ANALYTICS"
    },
    {
        "transcript": "List all active clients in our database",
        "intent": "LIST_CLIENTS"
    }
]


def seed_sample_data(conn, force: bool = False):
    """
    Populates sample data if tables are empty or if force=True.
    Returns summary of inserted records.
    """
    c = conn.cursor()
    client_count = c.execute("SELECT COUNT(*) FROM clients").fetchone()[0]

    if client_count > 0 and not force:
        return {"status": "skipped", "message": "Database already contains data."}

    if force:
        c.execute("DELETE FROM voice_commands")
        c.execute("DELETE FROM reminders")
        c.execute("DELETE FROM payments")
        c.execute("DELETE FROM invoices")
        c.execute("DELETE FROM clients")
        try:
            c.execute("DELETE FROM sqlite_sequence")
        except Exception:
            pass


    # 1. Insert Clients
    client_ids = []
    for client in SAMPLE_CLIENTS:
        cur = c.execute(
            "INSERT INTO clients (name, phone, email) VALUES (?, ?, ?)",
            (client["name"], client["phone"], client["email"])
        )
        client_ids.append(cur.lastrowid)

    # 2. Insert Invoices
    invoice_ids = []
    for inv in SAMPLE_INVOICES:
        cid = client_ids[inv["client_idx"] - 1]
        cur = c.execute(
            """INSERT INTO invoices
               (client_id, description, amount, due_date, upi_id, status, recurring, recurrence, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cid, inv["description"], inv["amount"], inv["due_date"],
             inv["upi_id"], inv["status"], inv["recurring"], inv["recurrence"], inv["created_at"])
        )
        invoice_ids.append(cur.lastrowid)

    # 3. Insert Payments
    for pmt in SAMPLE_PAYMENTS:
        iid = invoice_ids[pmt["invoice_idx"] - 1]
        c.execute(
            """INSERT INTO payments
               (invoice_id, amount, transaction_id, payment_date, source, raw_text)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (iid, pmt["amount"], pmt["transaction_id"], pmt["payment_date"], pmt["source"], pmt["raw_text"])
        )

    # 4. Insert Reminders
    for rem in SAMPLE_REMINDERS:
        iid = invoice_ids[rem["invoice_idx"] - 1]
        c.execute(
            """INSERT INTO reminders
               (invoice_id, reminder_type, scheduled_for, status, sent_at)
               VALUES (?, ?, ?, ?, ?)""",
            (iid, rem["reminder_type"], rem["scheduled_for"], rem["status"], rem["sent_at"])
        )

    # 5. Insert Voice Commands
    for vc in SAMPLE_VOICE_COMMANDS:
        c.execute(
            "INSERT INTO voice_commands (transcript, intent) VALUES (?, ?)",
            (vc["transcript"], vc["intent"])
        )

    conn.commit()

    return {
        "status": "success",
        "clients_added": len(client_ids),
        "invoices_added": len(invoice_ids),
        "payments_added": len(SAMPLE_PAYMENTS),
        "reminders_added": len(SAMPLE_REMINDERS),
        "voice_commands_added": len(SAMPLE_VOICE_COMMANDS)
    }
