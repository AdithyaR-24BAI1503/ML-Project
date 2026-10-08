"""
Database connection and session management.

Supports MySQL (via PyMySQL) and SQLite for local development
and testing by setting DB_ENGINE or DATABASE_URL in the environment.
"""
import os
import sqlite3
from pathlib import Path
from urllib.parse import urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

try:
    import pymysql
    import pymysql.cursors
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False

DB_ENGINE = os.getenv("DB_ENGINE", "").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatbiz.db")
DB_PATH = Path(__file__).resolve().parent.parent / "chatbiz.db"

IS_MYSQL = DB_ENGINE == "mysql" or DATABASE_URL.startswith("mysql")

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


class RowDict(dict):
    def __init__(self, d, keys=None):
        super().__init__(d)
        self._keys = keys or list(d.keys())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self[self._keys[key]]
        return super().__getitem__(key)


class CursorAdapter:
    def __init__(self, cursor, is_mysql=False):
        self.cursor = cursor
        self.is_mysql = is_mysql

    @property
    def lastrowid(self):
        return getattr(self.cursor, "lastrowid", None)

    @property
    def rowcount(self):
        return getattr(self.cursor, "rowcount", -1)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        if self.is_mysql and isinstance(row, dict):
            return RowDict(row)
        return row

    def fetchall(self):
        rows = self.cursor.fetchall()
        if not rows:
            return []
        if self.is_mysql and rows and isinstance(rows[0], dict):
            return [RowDict(r) for r in rows]
        return rows


class MySQLConnectionAdapter:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor(pymysql.cursors.DictCursor)

    def execute(self, sql, params=None):
        mysql_sql = sql.replace("?", "%s")
        if params is None:
            self.cursor.execute(mysql_sql)
        else:
            self.cursor.execute(mysql_sql, params)
        return CursorAdapter(self.cursor, is_mysql=True)

    def commit(self):
        self.conn.commit()

    def close(self):
        try:
            self.cursor.close()
        except Exception:
            pass
        try:
            self.conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        self.close()


def _create_mysql_connection():
    if not HAS_PYMYSQL:
        raise ImportError("PyMySQL package is required for MySQL connection.")
    if DATABASE_URL.startswith("mysql"):
        clean_url = DATABASE_URL.replace("mysql+pymysql://", "http://").replace("mysql://", "http://")
        parsed = urlparse(clean_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 3306
        user = parsed.username or "root"
        password = parsed.password or ""
        dbname = parsed.path.lstrip("/") or "chatbiz"
    else:
        host = os.getenv("MYSQL_HOST", "localhost")
        port = int(os.getenv("MYSQL_PORT", "3306"))
        user = os.getenv("MYSQL_USER", "root")
        password = os.getenv("MYSQL_PASSWORD", "")
        dbname = os.getenv("MYSQL_DATABASE", os.getenv("MYSQL_DB", "chatbiz"))

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=dbname,
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor
    )
    return MySQLConnectionAdapter(conn)


def get_connection():
    init_db()
    if IS_MYSQL:
        try:
            return _create_mysql_connection()
        except Exception as e:
            print(f"Warning: Failed to connect to MySQL ({e}). Falling back to SQLite.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    Base.metadata.create_all(bind=engine)

