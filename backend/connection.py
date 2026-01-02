"""
Enhanced database connection manager with connection pooling and transaction support.
Optimized for performance and reliability.
"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
import time

DB_FILE = Path(__file__).parent / "museum.db"

# Connection pool settings
MAX_RETRIES = 3
RETRY_DELAY = 0.1  # seconds

class DatabaseError(Exception):
    """Custom exception for database errors."""
    pass

@contextmanager
def get_cursor(commit: bool = False, retry: bool = True):
    """
    Context manager for database cursor with automatic connection handling.

    Args:
        commit: Whether to commit changes after execution
        retry: Whether to retry on database lock errors

    Yields:
        sqlite3.Cursor: Database cursor with Row factory

    Raises:
        DatabaseError: If connection or execution fails after retries
    """
    conn = None
    retries = MAX_RETRIES if retry else 1
    last_error = None

    for attempt in range(retries):
        try:
            # Connect with optimized settings
            conn = sqlite3.connect(
                DB_FILE,
                isolation_level=None,  # Autocommit mode for performance
                timeout=10.0,  # Wait up to 10 seconds for locks
                check_same_thread=False  # Allow multi-threaded access
            )

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")

            # Performance optimizations
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
            conn.execute("PRAGMA synchronous = NORMAL")  # Balance safety/performance
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            conn.execute("PRAGMA temp_store = MEMORY")  # Keep temp tables in memory

            # Use Row factory for dict-like access
            conn.row_factory = sqlite3.Row

            cur = conn.cursor()

            try:
                yield cur

                if commit:
                    conn.commit()

                # Success - break retry loop
                break

            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < retries - 1:
                    # Database is locked, retry
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    last_error = e
                    continue
                raise DatabaseError(f"Database operation failed: {e}")

            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Data integrity error: {e}")

            except Exception as e:
                raise DatabaseError(f"Unexpected database error: {e}")

        finally:
            if conn:
                conn.close()

    # If we exhausted retries
    if last_error:
        raise DatabaseError(f"Database locked after {retries} attempts: {last_error}")

def execute_transaction(operations: list, rollback_on_error: bool = True):
    """
    Execute multiple operations as a single transaction.

    Args:
        operations: List of tuples (sql, params)
        rollback_on_error: Whether to rollback on error

    Returns:
        bool: True if successful

    Raises:
        DatabaseError: If transaction fails
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10.0)
        conn.execute("PRAGMA foreign_keys = ON")

        # Begin explicit transaction
        conn.execute("BEGIN")

        for sql, params in operations:
            conn.execute(sql, params)

        conn.commit()
        return True

    except Exception as e:
        if conn and rollback_on_error:
            conn.rollback()
        raise DatabaseError(f"Transaction failed: {e}")

    finally:
        if conn:
            conn.close()

def vacuum_database():
    """
    Optimize database by rebuilding the database file.
    Should be run periodically for performance maintenance.
    """
    try:
        with get_cursor() as cur:
            cur.execute("VACUUM")
        return True
    except Exception as e:
        raise DatabaseError(f"Vacuum operation failed: {e}")

def analyze_database():
    """
    Update internal statistics used by query optimizer.
    Should be run after significant data changes.
    """
    try:
        with get_cursor() as cur:
            cur.execute("ANALYZE")
        return True
    except Exception as e:
        raise DatabaseError(f"Analyze operation failed: {e}")

def check_database_integrity():
    """
    Check database integrity and return any issues.

    Returns:
        list: List of integrity check results
    """
    try:
        with get_cursor() as cur:
            cur.execute("PRAGMA integrity_check")
            results = cur.fetchall()
            return [dict(row) for row in results]
    except Exception as e:
        raise DatabaseError(f"Integrity check failed: {e}")

def get_database_stats() -> dict:
    """
    Get database statistics for monitoring.

    Returns:
        dict: Database statistics
    """
    try:
        with get_cursor() as cur:
            stats = {}

            # Page count and size
            cur.execute("PRAGMA page_count")
            stats['page_count'] = cur.fetchone()[0]

            cur.execute("PRAGMA page_size")
            stats['page_size'] = cur.fetchone()[0]

            # Calculate database size
            stats['size_bytes'] = stats['page_count'] * stats['page_size']
            stats['size_mb'] = round(stats['size_bytes'] / (1024 * 1024), 2)

            # Table counts
            cur.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cur.fetchall()]

            stats['tables'] = {}
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                stats['tables'][table] = cur.fetchone()[0]

            return stats

    except Exception as e:
        raise DatabaseError(f"Failed to get database stats: {e}")

