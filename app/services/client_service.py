"""
Client Management Business Service
"""
from ..database import get_connection

def add_client(name: str, phone: str = None, email: str = None):
    try:
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO clients(name, phone, email) VALUES (?, ?, ?)",
                (name.strip(), phone, email)
            )
            conn.commit()
            return dict(conn.execute(
                "SELECT * FROM clients WHERE id=?", (cur.lastrowid,)
            ).fetchone())
    except Exception as e:
        if "UNIQUE" in str(e).upper():
            raise ValueError("A client with that name already exists.")
        raise

def list_clients():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM clients ORDER BY name ASC"
        ).fetchall()]

def find_client(name: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM clients WHERE lower(name)=lower(?)", (name.strip(),)
        ).fetchone()
        return dict(row) if row else None

def update_client(name: str, field: str, value: str):
    if field not in {"phone", "email"}:
        raise ValueError("Only phone and email can be updated.")
    with get_connection() as conn:
        cur = conn.execute(
            f"UPDATE clients SET {field}=? WHERE lower(name)=lower(?)",
            (value, name.strip())
        )
        conn.commit()
    return find_client(name) if cur.rowcount else None

def delete_client(name: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM clients WHERE lower(name)=lower(?)", (name.strip(),)
        )
        conn.commit()
        return cur.rowcount > 0
