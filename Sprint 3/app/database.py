import os
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

try:
    import pymysql
    import pymysql.cursors
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False

DB_PATH = Path(__file__).resolve().parent.parent / "chatbiz.db"
_initialized = False

DB_ENGINE = os.getenv("DB_ENGINE", "").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatbiz.db")

IS_MYSQL = DB_ENGINE == "mysql" or DATABASE_URL.startswith("mysql")


class RowDict(dict):
    """Subclass of dict to support integer index positioning like sqlite3.Row for backward compatibility."""
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


def _init_sqlite_tables(conn):
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


def _init_mysql_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(120) NOT NULL UNIQUE,
            phone VARCHAR(20),
            email VARCHAR(120),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            client_id INT,
            description VARCHAR(255) NOT NULL DEFAULT '',
            amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
            due_date VARCHAR(50),
            upi_id VARCHAR(100),
            status VARCHAR(30) DEFAULT 'Pending',
            pdf_path VARCHAR(255),
            recurring INT DEFAULT 0,
            recurrence VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            invoice_id INT,
            amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
            transaction_id VARCHAR(100),
            payment_date VARCHAR(50),
            source VARCHAR(50) DEFAULT 'manual',
            raw_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            invoice_id INT,
            reminder_type VARCHAR(50),
            scheduled_for VARCHAR(50),
            status VARCHAR(30) DEFAULT 'PENDING',
            sent_at VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS voice_commands (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transcript TEXT,
            intent VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    conn.commit()


def _init_tables(conn):
    if IS_MYSQL:
        _init_mysql_tables(conn)
    else:
        _init_sqlite_tables(conn)


def get_connection():
    global _initialized
    if IS_MYSQL:
        try:
            conn = _create_mysql_connection()
            if not _initialized:
                _init_tables(conn)
                _initialized = True
            return conn
        except Exception as e:
            print(f"Warning: Failed to connect to MySQL ({e}). Falling back to SQLite.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if not _initialized:
        _init_tables(conn)
        _initialized = True
    return conn


def init_db():
    global _initialized
    conn = get_connection()
    if not IS_MYSQL:
        _init_tables(conn)
        conn.close()
    _initialized = True
