import sqlite3

DB_NAME = "museum.db"


def reset_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # IMPORTANT: Delete child tables first (FK dependency order)
    cursor.executescript("""
        DELETE FROM visit;
        DELETE FROM conservation;
        DELETE FROM exhibit;
        DELETE FROM visitor;
        DELETE FROM museum;
    """)

    # Reset AUTOINCREMENT counters (SQLite specific)
    cursor.execute("DELETE FROM sqlite_sequence")

    conn.commit()
    conn.close()

    print("Database reset successfully.")


if __name__ == "__main__":
    reset_database()
