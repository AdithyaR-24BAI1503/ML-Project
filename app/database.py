"""
Unified Database connection and session management for ChatBiz.
Supports local SQLite with row-factory dict access and optional MySQL connection.
Provides both sqlite3 helper connections and SQLAlchemy session dependency.
"""
import os
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent / "chatbiz.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

_initialized = False

def get_db():
    """FastAPI dependency yielding a SQLAlchemy DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _init_tables(conn):
    """Initializes unified relational schema across all ChatBiz modules."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone_whatsapp TEXT NOT NULL UNIQUE,
            business_name TEXT,
            gst_number TEXT,
            subscription_plan TEXT DEFAULT 'free',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            phone TEXT,
            email TEXT,
            address TEXT,
            notes TEXT,
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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            sender TEXT NOT NULL,
            client_id INTEGER,
            content TEXT NOT NULL,
            metadata_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Lazy-import to prevent circular dependency
    from .seed_data import seed_sample_data
    seed_sample_data(conn, force=False)

def get_connection():
    """
    Returns an active SQLite connection with Row factory enabled.
    Initializes tables and seed data automatically on first invocation.
    """
    global _initialized
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if not _initialized:
        _init_tables(conn)
        _initialized = True
    return conn

def init_db(force_seed: bool = False):
    """Initializes tables and optionally force-resets sample data."""
    global _initialized
    # Create SQLAlchemy models if used
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    with sqlite3.connect(DB_PATH) as conn:
        _init_tables(conn)
        if force_seed:
            from .seed_data import seed_sample_data
            seed_sample_data(conn, force=True)
    _initialized = True
