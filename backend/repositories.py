from typing import List, Tuple
from .connection import get_cursor

# ---------- Internal helpers -------------------------------------------------
def _query_fetchall(sql: str, params: tuple = ()) -> List[dict]:
    """Fetch all results from a query as dict-like rows."""
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()

def _query_execute(sql: str, params: tuple = ()) -> None:
    """Execute a write query with commit."""
    with get_cursor(commit=True) as cur:
        cur.execute(sql, params)


# ---------- Museum repository ------------------------------------------------
class MuseumRepository:
    @staticmethod
    def create(name: str, city: str) -> None:
        """Add a new museum (ignores duplicates)."""
        _query_execute(
            "INSERT OR IGNORE INTO museum(name, city) VALUES (?, ?)",
            (name, city)
        )

    @staticmethod
    def all() -> List[dict]:
        """Return all museums sorted by name."""
        return _query_fetchall("SELECT museum_id, name, city FROM museum ORDER BY name")


# ---------- Exhibit / Item repository ---------------------------------------
class ExhibitRepository:
    @staticmethod
    def add(museum_id: int, title: str, category: str, acquired: str) -> None:
        """Insert a new exhibit into a museum."""
        _query_execute(
            "INSERT INTO item(museum_id, title, category, acquired) VALUES (?, ?, ?, ?)",
            (museum_id, title, category, acquired)
        )

    @staticmethod
    def top_by_maintenance() -> List[Tuple[str, int]]:
        """Return exhibits ranked by number of maintenance actions."""
        sql = """
        SELECT title, COUNT(upkeep_id) AS maintenance_count
        FROM item
        LEFT JOIN upkeep USING(item_id)
        GROUP BY item_id
        ORDER BY maintenance_count DESC, title
        """
        return [(row["title"], row["maintenance_count"]) for row in _query_fetchall(sql)]


# ---------- Guest / Visitor repository --------------------------------------
class VisitorRepository:
    @staticmethod
    def register(full_name: str, email: str) -> None:
        """Register a new visitor (ignores duplicates)."""
        _query_execute(
            "INSERT OR IGNORE INTO guest(full_name, email) VALUES (?, ?)",
            (full_name, email)
        )

    @staticmethod
    def record_visit(guest_id: int, museum_id: int, visited_on: str) -> None:
        """Log a museum visit for a visitor."""
        _query_execute(
            "INSERT INTO visit(guest_id, museum_id, visited_on) VALUES (?, ?, ?)",
            (guest_id, museum_id, visited_on)
        )

    @staticmethod
    def activity_summary() -> List[Tuple[str, int]]:
        """Return visitors ranked by number of museums visited."""
        sql = """
        SELECT full_name, COUNT(DISTINCT museum_id) AS museums_visited
        FROM guest
        JOIN visit USING(guest_id)
        GROUP BY guest_id
        ORDER BY museums_visited DESC, full_name
        """
        return [(row["full_name"], row["museums_visited"]) for row in _query_fetchall(sql)]


# ---------- Maintenance / Upkeep repository ---------------------------------
class MaintenanceRepository:
    @staticmethod
    def schedule(item_id: int, task: str, done_on: str, technician: str) -> None:
        """Add a maintenance task for an exhibit."""
        _query_execute(
            "INSERT INTO upkeep(item_id, task, done_on, technician) VALUES (?, ?, ?, ?)",
            (item_id, task, done_on, technician)
        )

    @staticmethod
    def summary() -> List[Tuple[str, int]]:
        """Return the number of maintenance actions per exhibit."""
        sql = """
        SELECT title, COUNT(upkeep_id) AS total_actions
        FROM item
        JOIN upkeep USING(item_id)
        GROUP BY item_id
        ORDER BY total_actions DESC
        """
        return [(row["title"], row["total_actions"]) for row in _query_fetchall(sql)]
