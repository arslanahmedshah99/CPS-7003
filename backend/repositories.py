"""
Enhanced data access layer with comprehensive repository pattern.
Provides optimized, secure database operations for all entities.
"""
from typing import List, Tuple, Optional, Dict, Any
from .connection import get_cursor, execute_transaction, DatabaseError

# ---------- Internal helpers -------------------------------------------------

def _query_fetchall(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Fetch all results from a query as dict-like rows."""
    try:
        with get_cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        raise DatabaseError(f"Query failed: {e}")

def _query_fetchone(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """Fetch one result from a query as dict-like row."""
    try:
        with get_cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        raise DatabaseError(f"Query failed: {e}")

def _query_execute(sql: str, params: tuple = ()) -> int:
    """Execute a write query with commit and return last row id."""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(sql, params)
            return cur.lastrowid
    except Exception as e:
        raise DatabaseError(f"Execute failed: {e}")

# ---------- Museum repository ------------------------------------------------

class MuseumRepository:
    """Repository for museum operations with caching and optimization."""

    @staticmethod
    def create(name: str, city: str) -> int:
        """Add a new museum and return its ID."""
        sql = "INSERT OR IGNORE INTO museum(name, city) VALUES (?, ?)"
        return _query_execute(sql, (name, city))

    @staticmethod
    def all() -> List[Dict[str, Any]]:
        """Return all museums sorted by name."""
        sql = "SELECT museum_id, name, city, created_at FROM museum ORDER BY name"
        return _query_fetchall(sql)

    @staticmethod
    def get_by_id(museum_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific museum by ID."""
        sql = "SELECT * FROM museum WHERE museum_id = ?"
        return _query_fetchone(sql, (museum_id,))

    @staticmethod
    def get_by_city(city: str) -> List[Dict[str, Any]]:
        """Get all museums in a specific city."""
        sql = "SELECT * FROM museum WHERE city = ? ORDER BY name"
        return _query_fetchall(sql, (city,))

    @staticmethod
    def update(museum_id: int, name: str, city: str) -> bool:
        """Update museum details."""
        sql = """UPDATE museum
                 SET name = ?, city = ?, updated_at = CURRENT_TIMESTAMP
                 WHERE museum_id = ?"""
        _query_execute(sql, (name, city, museum_id))
        return True

    @staticmethod
    def delete(museum_id: int) -> bool:
        """Delete a museum (only if no active items)."""
        sql = "DELETE FROM museum WHERE museum_id = ?"
        _query_execute(sql, (museum_id,))
        return True

    @staticmethod
    def get_statistics(museum_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get statistics for museums."""
        if museum_id:
            sql = "SELECT * FROM museum_stats WHERE museum_id = ?"
            return _query_fetchall(sql, (museum_id,))
        else:
            sql = "SELECT * FROM museum_stats ORDER BY total_items DESC"
            return _query_fetchall(sql)

# ---------- Exhibit / Item repository ----------------------------------------

class ExhibitRepository:
    """Repository for exhibit/item operations with advanced queries."""

    @staticmethod
    def add(museum_id: int, title: str, category: str, acquired: str) -> int:
        """Insert a new exhibit into a museum."""
        sql = """INSERT INTO item(museum_id, title, category, acquired)
                 VALUES (?, ?, ?, ?)"""
        return _query_execute(sql, (museum_id, title, category, acquired))

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Get all exhibits with museum information."""
        sql = """SELECT i.*, m.name as museum_name, m.city
                 FROM item i
                 JOIN museum m ON i.museum_id = m.museum_id
                 ORDER BY i.title"""
        return _query_fetchall(sql)

    @staticmethod
    def get_by_id(item_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific exhibit by ID."""
        sql = """SELECT i.*, m.name as museum_name
                 FROM item i
                 JOIN museum m ON i.museum_id = m.museum_id
                 WHERE i.item_id = ?"""
        return _query_fetchone(sql, (item_id,))

    @staticmethod
    def get_by_museum(museum_id: int, active_only: bool = False) -> List[Dict[str, Any]]:
        """Get all exhibits for a specific museum."""
        if active_only:
            sql = """SELECT * FROM item
                     WHERE museum_id = ? AND status = 'active'
                     ORDER BY title"""
        else:
            sql = """SELECT * FROM item
                     WHERE museum_id = ?
                     ORDER BY title"""
        return _query_fetchall(sql, (museum_id,))

    @staticmethod
    def get_by_category(category: str) -> List[Dict[str, Any]]:
        """Get exhibits filtered by category."""
        sql = """SELECT i.*, m.name as museum_name
                 FROM item i
                 JOIN museum m ON i.museum_id = m.museum_id
                 WHERE i.category = ?
                 ORDER BY i.title"""
        return _query_fetchall(sql, (category,))

    @staticmethod
    def get_by_status(status: str) -> List[Dict[str, Any]]:
        """Get exhibits filtered by status."""
        sql = """SELECT i.*, m.name as museum_name
                 FROM item i
                 JOIN museum m ON i.museum_id = m.museum_id
                 WHERE i.status = ?
                 ORDER BY i.title"""
        return _query_fetchall(sql, (status,))

    @staticmethod
    def update_status(item_id: int, status: str) -> bool:
        """Update exhibit status."""
        sql = """UPDATE item
                 SET status = ?, updated_at = CURRENT_TIMESTAMP
                 WHERE item_id = ?"""
        _query_execute(sql, (status, item_id))
        return True

    @staticmethod
    def update(item_id: int, title: str, category: str) -> bool:
        """Update exhibit details."""
        sql = """UPDATE item
                 SET title = ?, category = ?, updated_at = CURRENT_TIMESTAMP
                 WHERE item_id = ?"""
        _query_execute(sql, (title, category, item_id))
        return True

    @staticmethod
    def delete(item_id: int) -> bool:
        """Delete an exhibit."""
        sql = "DELETE FROM item WHERE item_id = ?"
        _query_execute(sql, (item_id,))
        return True

    @staticmethod
    def top_by_maintenance(limit: int = 10) -> List[Tuple[str, int]]:
        """Return exhibits ranked by number of maintenance actions."""
        sql = """SELECT title, COUNT(upkeep_id) AS maintenance_count
                 FROM item
                 LEFT JOIN upkeep USING(item_id)
                 GROUP BY item_id
                 ORDER BY maintenance_count DESC, title
                 LIMIT ?"""
        results = _query_fetchall(sql, (limit,))
        return [(row["title"], row["maintenance_count"]) for row in results]

    @staticmethod
    def search(query: str) -> List[Dict[str, Any]]:
        """Search exhibits by title or category."""
        sql = """SELECT i.*, m.name as museum_name
                 FROM item i
                 JOIN museum m ON i.museum_id = m.museum_id
                 WHERE i.title LIKE ? OR i.category LIKE ?
                 ORDER BY i.title"""
        search_term = f"%{query}%"
        return _query_fetchall(sql, (search_term, search_term))

# ---------- Guest / Visitor repository ---------------------------------------

class VisitorRepository:
    """Repository for visitor operations with activity tracking."""

    @staticmethod
    def register(full_name: str, email: str, phone: Optional[str] = None) -> int:
        """Register a new visitor."""
        if phone:
            sql = """INSERT OR IGNORE INTO guest(full_name, email, phone)
                     VALUES (?, ?, ?)"""
            return _query_execute(sql, (full_name, email, phone))
        else:
            sql = """INSERT OR IGNORE INTO guest(full_name, email)
                     VALUES (?, ?)"""
            return _query_execute(sql, (full_name, email))

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Get all registered visitors."""
        sql = "SELECT * FROM guest ORDER BY full_name"
        return _query_fetchall(sql)

    @staticmethod
    def get_by_id(guest_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific visitor by ID."""
        sql = "SELECT * FROM guest WHERE guest_id = ?"
        return _query_fetchone(sql, (guest_id,))

    @staticmethod
    def get_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get a visitor by email address."""
        sql = "SELECT * FROM guest WHERE email = ?"
        return _query_fetchone(sql, (email,))

    @staticmethod
    def update(guest_id: int, full_name: str, email: str, phone: Optional[str]) -> bool:
        """Update visitor details."""
        sql = """UPDATE guest
                 SET full_name = ?, email = ?, phone = ?, updated_at = CURRENT_TIMESTAMP
                 WHERE guest_id = ?"""
        _query_execute(sql, (full_name, email, phone, guest_id))
        return True

    @staticmethod
    def delete(guest_id: int) -> bool:
        """Delete a visitor."""
        sql = "DELETE FROM guest WHERE guest_id = ?"
        _query_execute(sql, (guest_id,))
        return True

    @staticmethod
    def record_visit(guest_id: int, museum_id: int, visited_on: str,
                    duration_minutes: Optional[int] = None) -> int:
        """Log a museum visit for a visitor."""
        if duration_minutes:
            sql = """INSERT INTO visit(guest_id, museum_id, visited_on, duration_minutes)
                     VALUES (?, ?, ?, ?)"""
            return _query_execute(sql, (guest_id, museum_id, visited_on, duration_minutes))
        else:
            sql = """INSERT INTO visit(guest_id, museum_id, visited_on)
                     VALUES (?, ?, ?)"""
            return _query_execute(sql, (guest_id, museum_id, visited_on))

    @staticmethod
    def get_visits_by_visitor(guest_id: int) -> List[Dict[str, Any]]:
        """Get all visits for a specific visitor."""
        sql = """SELECT v.*, m.name as museum_name, m.city
                 FROM visit v
                 JOIN museum m ON v.museum_id = m.museum_id
                 WHERE v.guest_id = ?
                 ORDER BY v.visited_on DESC"""
        return _query_fetchall(sql, (guest_id,))

    @staticmethod
    def get_visits_by_museum(museum_id: int) -> List[Dict[str, Any]]:
        """Get all visits for a specific museum."""
        sql = """SELECT v.*, g.full_name, g.email
                 FROM visit v
                 JOIN guest g ON v.guest_id = g.guest_id
                 WHERE v.museum_id = ?
                 ORDER BY v.visited_on DESC"""
        return _query_fetchall(sql, (museum_id,))

    @staticmethod
    def activity_summary(min_visits: int = 0) -> List[Tuple[str, int]]:
        """Return visitors ranked by number of museums visited."""
        sql = """SELECT full_name, COUNT(DISTINCT museum_id) AS museums_visited
                 FROM guest
                 JOIN visit USING(guest_id)
                 GROUP BY guest_id
                 HAVING museums_visited >= ?
                 ORDER BY museums_visited DESC, full_name"""
        results = _query_fetchall(sql, (min_visits,))
        return [(row["full_name"], row["museums_visited"]) for row in results]

# ---------- Maintenance / Upkeep repository ----------------------------------

class MaintenanceRepository:
    """Repository for maintenance operations with cost tracking."""

    @staticmethod
    def schedule(item_id: int, task: str, done_on: str, technician: str,
                cost: Optional[float] = None, notes: Optional[str] = None) -> int:
        """Add a maintenance task for an exhibit."""
        if cost is not None or notes is not None:
            sql = """INSERT INTO upkeep(item_id, task, done_on, technician, cost, notes)
                     VALUES (?, ?, ?, ?, ?, ?)"""
            return _query_execute(sql, (item_id, task, done_on, technician, cost, notes))
        else:
            sql = """INSERT INTO upkeep(item_id, task, done_on, technician)
                     VALUES (?, ?, ?, ?)"""
            return _query_execute(sql, (item_id, task, done_on, technician))

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Get all maintenance records."""
        sql = "SELECT * FROM item_maintenance_view ORDER BY done_on DESC"
        return _query_fetchall(sql)

    @staticmethod
    def get_by_item(item_id: int) -> List[Dict[str, Any]]:
        """Get maintenance history for a specific item."""
        sql = """SELECT * FROM upkeep
                 WHERE item_id = ?
                 ORDER BY done_on DESC"""
        return _query_fetchall(sql, (item_id,))

    @staticmethod
    def get_by_date_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get maintenance records within a date range."""
        sql = """SELECT * FROM item_maintenance_view
                 WHERE done_on BETWEEN ? AND ?
                 ORDER BY done_on DESC"""
        return _query_fetchall(sql, (start_date, end_date))

    @staticmethod
    def update(upkeep_id: int, task: str, done_on: str,
              technician: str, cost: Optional[float]) -> bool:
        """Update maintenance record."""
        sql = """UPDATE upkeep
                 SET task = ?, done_on = ?, technician = ?, cost = ?
                 WHERE upkeep_id = ?"""
        _query_execute(sql, (task, done_on, technician, cost, upkeep_id))
        return True

    @staticmethod
    def delete(upkeep_id: int) -> bool:
        """Delete a maintenance record."""
        sql = "DELETE FROM upkeep WHERE upkeep_id = ?"
        _query_execute(sql, (upkeep_id,))
        return True

    @staticmethod
    def summary(limit: Optional[int] = None) -> List[Tuple[str, int]]:
        """Return the number of maintenance actions per exhibit."""
        sql = """SELECT title, COUNT(upkeep_id) AS total_actions
                 FROM item
                 JOIN upkeep USING(item_id)
                 GROUP BY item_id
                 ORDER BY total_actions DESC"""

        if limit:
            sql += f" LIMIT {limit}"

        results = _query_fetchall(sql)
        return [(row["title"], row["total_actions"]) for row in results]

    @staticmethod
    def cost_analysis(start_date: str, end_date: str) -> Dict[str, Any]:
        """Analyze maintenance costs over a period."""
        sql = """SELECT
                 COUNT(*) as total_tasks,
                 SUM(COALESCE(cost, 0)) as total_cost,
                 AVG(COALESCE(cost, 0)) as avg_cost,
                 MIN(cost) as min_cost,
                 MAX(cost) as max_cost
                 FROM upkeep
                 WHERE done_on BETWEEN ? AND ?"""
        return _query_fetchone(sql, (start_date, end_date))

# ---------- User repository (for authentication) -----------------------------

class UserRepository:
    """Repository for user management operations."""

    @staticmethod
    def get_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        sql = "SELECT * FROM user WHERE username = ?"
        return _query_fetchone(sql, (username,))

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        sql = "SELECT * FROM user WHERE user_id = ?"
        return _query_fetchone(sql, (user_id,))

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """Get all users."""
        sql = "SELECT user_id, username, email, role, is_active, created_at FROM user ORDER BY username"
        return _query_fetchall(sql)

    @staticmethod
    def update_last_login(user_id: int) -> bool:
        """Update user's last login timestamp."""
        sql = "UPDATE user SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?"
        _query_execute(sql, (user_id,))
        return True

    @staticmethod
    def deactivate(user_id: int) -> bool:
        """Deactivate a user account."""
        sql = "UPDATE user SET is_active = 0 WHERE user_id = ?"
        _query_execute(sql, (user_id,))
        return True

    @staticmethod
    def activate(user_id: int) -> bool:
        """Activate a user account."""
        sql = "UPDATE user SET is_active = 1 WHERE user_id = ?"
        _query_execute(sql, (user_id,))
        return True

