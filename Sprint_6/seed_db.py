"""
CLI helper to seed or reset sample data in ChatBiz database.
Run from repository or Sprint_6 directory:
    python seed_db.py [--reset]
"""

import sys
import argparse
from pathlib import Path

# Add Sprint_6 to sys.path so app modules can be imported
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from app.database import get_connection, init_db
from app.seed_data import seed_sample_data

def main():
    parser = argparse.ArgumentParser(description="ChatBiz Database Seeder")
    parser.add_argument("--reset", action="store_true", help="Clear existing data and force re-seed")
    args = parser.parse_args()

    init_db()
    with get_connection() as conn:
        result = seed_sample_data(conn, force=args.reset)
        c = conn.cursor()
        print("=== ChatBiz Database Seeder ===")
        print(f"Status: {result.get('status')}")
        if "message" in result:
            print(f"Message: {result['message']}")
        print("Current DB Counts:")
        print(f" - Clients:        {c.execute('SELECT COUNT(*) FROM clients').fetchone()[0]}")
        print(f" - Invoices:       {c.execute('SELECT COUNT(*) FROM invoices').fetchone()[0]}")
        print(f" - Payments:       {c.execute('SELECT COUNT(*) FROM payments').fetchone()[0]}")
        print(f" - Reminders:      {c.execute('SELECT COUNT(*) FROM reminders').fetchone()[0]}")
        print(f" - Voice Commands: {c.execute('SELECT COUNT(*) FROM voice_commands').fetchone()[0]}")
        print("================================")

if __name__ == "__main__":
    main()
