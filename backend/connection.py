import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_FILE = Path(__file__).with_name("museum.db")

@contextmanager
def get_cursor(commit: bool = False):
    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()
