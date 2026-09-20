from .database import get_connection

def add_client(name, phone=None, email=None):
    try:
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO clients(name, phone, email) VALUES (?, ?, ?)",
                (name, phone, email)
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
            "SELECT * FROM clients ORDER BY id DESC"
        ).fetchall()]

def find_client(name):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM clients WHERE lower(name)=lower(?)", (name,)
        ).fetchone()
        return dict(row) if row else None

def update_client(name, field, value):
    if field not in {"phone", "email"}:
        raise ValueError("Only phone and email can be updated.")
    with get_connection() as conn:
        cur = conn.execute(
            f"UPDATE clients SET {field}=? WHERE lower(name)=lower(?)",
            (value, name)
        )
        conn.commit()
    return find_client(name) if cur.rowcount else None

def delete_client(name):
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM clients WHERE lower(name)=lower(?)", (name,)
        )
        conn.commit()
        return cur.rowcount > 0
