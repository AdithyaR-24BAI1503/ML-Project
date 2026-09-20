"""
Database connection and session management.

Uses SQLite for local development (per Lab1 Software Requirements)
and is ready to switch to PostgreSQL in production by changing
DATABASE_URL in the environment.
"""
import os
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatbiz.db")
DB_PATH = Path(__file__).resolve().parent.parent / "chatbiz.db"

# SQLite needs this connect_arg; Postgres doesn't, so only set it conditionally.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_connection():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    Base.metadata.create_all(bind=engine)

