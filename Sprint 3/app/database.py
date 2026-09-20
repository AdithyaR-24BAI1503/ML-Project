import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "chatbiz.db"
_initialized = False

def _init_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            phone TEXT,
            email TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            description TEXT NOT NULL DEFAULT '',
            amount REAL NOT NULL DEFAULT 0,
            due_date TEXT,
            upi_id TEXT,
            status TEXT DEFAULT 'Pending',
            pdf_path TEXT,
            recurring INTEGER DEFAULT 0,
            recurrence TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            amount REAL NOT NULL DEFAULT 0,
            transaction_id TEXT,
            payment_date TEXT,
            source TEXT DEFAULT 'manual',
            raw_text TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            reminder_type TEXT,
            scheduled_for TEXT,
            status TEXT DEFAULT 'PENDING',
            sent_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS voice_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transcript TEXT,
            intent TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

def get_connection():
    global _initialized
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if not _initialized:
        _init_tables(conn)
        _initialized = True
    return conn

def init_db():
    global _initialized
    with sqlite3.connect(DB_PATH) as conn:
        _init_tables(conn)
    _initialized = True
