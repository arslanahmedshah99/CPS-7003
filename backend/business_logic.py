"""
Business logic layer - encapsulates business rules and orchestrates operations.
This layer sits between the presentation layer and data access layer.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from . import repositories as repos
from .security import (
    AuthorizationManager, InputValidator, ValidationError,
    AuthorizationError, AuditLogger
)

class BusinessException(Exception):
    """Custom exception for business logic errors."""
    pass

class MuseumService:
    """Business logic for museum operations."""

    @staticmethod
    def create_museum(name: str, city: str, user_role: str, user_id: int) -> None:
        """Create a new museum with business validation."""
        AuthorizationManager.require_permission(user_role, 'create')

        name = InputValidator.validate_name(name, "Museum name")
        city = InputValidator.validate_name(city, "City")

        repos.MuseumRepository.create(name, city)
        AuditLogger.log_action(user_id, 'CREATE', 'museum', None, None, f"name={name},city={city}")

    @staticmethod
    def get_all_museums(user_role: str) -> List[dict]:
        """Get all museums - available to all authenticated users."""
        AuthorizationManager.require_permission(user_role, 'read')
        return repos.MuseumRepository.all()

    @staticmethod
    def get_museum_statistics() -> List[Dict]:
        """Get comprehensive statistics for all museums."""
        from .connection import get_cursor
        with get_cursor() as cur:
            cur.execute("SELECT * FROM museum_stats ORDER BY total_items DESC")
            return cur.fetchall()

    @staticmethod
    def validate_museum_capacity(museum_id: int, max_items: int = 1000) -> bool:
        """Check if museum has reached maximum capacity."""
        from .connection import get_cursor
        with get_cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as count FROM item WHERE museum_id = ? AND status = 'active'",
                (museum_id,)
            )
            count = cur.fetchone()['count']
            return count < max_items

class ExhibitService:
    """Business logic for exhibit/item operations."""

    @staticmethod
    def add_exhibit(museum_id: int, title: str, category: str, acquired: str,
                    user_role: str, user_id: int) -> None:
        """Add a new exhibit with business validation."""
        AuthorizationManager.require_permission(user_role, 'create')

        # Validate inputs
        museum_id = InputValidator.validate_positive_int(museum_id, "Museum ID")
        title = InputValidator.validate_name(title, "Exhibit title")
        category = InputValidator.validate_name(category, "Category")
        acquired = InputValidator.validate_date(acquired)

        # Business rule: Check museum capacity
        if not MuseumService.validate_museum_capacity(museum_id):
            raise BusinessException(f"Museum {museum_id} has reached maximum capacity")

        # Business rule: Acquisition date cannot be in the future
        if datetime.strptime(acquired, '%Y-%m-%d') > datetime.now():
            raise ValidationError("Acquisition date cannot be in the future")

        repos.ExhibitRepository.add(museum_id, title, category, acquired)
        AuditLogger.log_action(
            user_id, 'CREATE', 'item', None, None,
            f"museum_id={museum_id},title={title}"
        )

    @staticmethod
    def get_exhibits_by_category(category: str, user_role: str) -> List[dict]:
        """Get exhibits filtered by category."""
        AuthorizationManager.require_permission(user_role, 'read')

        from .connection import get_cursor
        with get_cursor() as cur:
            cur.execute(
                """SELECT i.*, m.name as museum_name
                   FROM item i
                   JOIN museum m ON i.museum_id = m.museum_id
                   WHERE i.category = ?
                   ORDER BY i.title""",
                (category,)
            )
            return cur.fetchall()

    @staticmethod
    def get_popular_exhibits(limit: int = 10) -> List[Tuple[str, int]]:
        """Get exhibits that need most maintenance (indicator of importance/use)."""
        return repos.ExhibitRepository.top_by_maintenance()[:limit]

    @staticmethod
    def change_exhibit_status(item_id: int, new_status: str, user_role: str, user_id: int) -> None:
        """Change exhibit status with authorization."""
        AuthorizationManager.require_permission(user_role, 'update')

        valid_statuses = ['active', 'on_loan', 'in_restoration', 'retired']
        if new_status not in valid_statuses:
            raise ValidationError(f"Invalid status. Must be one of: {valid_statuses}")

        from .connection import get_cursor
        with get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE item SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE item_id = ?",
                (new_status, item_id)
            )

        AuditLogger.log_action(user_id, 'UPDATE', 'item', item_id, None, f"status={new_status}")

class VisitorService:
    """Business logic for visitor operations."""

    @staticmethod
    def register_visitor(full_name: str, email: str, phone: Optional[str],
                        user_role: str, user_id: int) -> None:
        """Register a new visitor with validation."""
        AuthorizationManager.require_permission(user_role, 'create')

        full_name = InputValidator.validate_name(full_name, "Full name")
        email = InputValidator.validate_email(email)

        if phone:
            phone = InputValidator.sanitize_string(phone, 20)

        repos.VisitorRepository.register(full_name, email)
        AuditLogger.log_action(user_id, 'CREATE', 'guest', None, None, f"name={full_name}")

    @staticmethod
    def record_visit(guest_id: int, museum_id: int, visited_on: str,
                    duration_minutes: Optional[int], user_role: str, user_id: int) -> None:
        """Record a museum visit with business validation."""
        AuthorizationManager.require_permission(user_role, 'create_visits')

        guest_id = InputValidator.validate_positive_int(guest_id, "Guest ID")
        museum_id = InputValidator.validate_positive_int(museum_id, "Museum ID")
        visited_on = InputValidator.validate_date(visited_on)

        # Business rule: Visit date cannot be in the future
        if datetime.strptime(visited_on, '%Y-%m-%d') > datetime.now():
            raise ValidationError("Visit date cannot be in the future")

        repos.VisitorRepository.record_visit(guest_id, museum_id, visited_on)
        AuditLogger.log_action(
            user_id, 'CREATE', 'visit', None, None,
            f"guest_id={guest_id},museum_id={museum_id}"
        )

    @staticmethod
    def get_frequent_visitors(min_visits: int = 5) -> List[Dict]:
        """Get visitors who have visited museums multiple times."""
        from .connection import get_cursor
        with get_cursor() as cur:
            cur.execute(
                """SELECT * FROM visitor_activity
                   WHERE total_visits >= ?
                   ORDER BY total_visits DESC""",
                (min_visits,)
            )
            return cur.fetchall()

    @staticmethod
    def get_visitor_recommendations(guest_id: int) -> List[Dict]:
        """Recommend museums based on visitor's history and preferences."""
        from .connection import get_cursor
        with get_cursor() as cur:
            # Find museums similar to those the visitor has visited
            cur.execute(
                """SELECT DISTINCT m.museum_id, m.name, m.city,
                   COUNT(i.item_id) as item_count
                   FROM museum m
                   JOIN item i ON m.museum_id = i.museum_id
                   WHERE m.museum_id NOT IN (
                       SELECT museum_id FROM visit WHERE guest_id = ?
                   )
                   AND i.category IN (
                       SELECT DISTINCT i2.category
                       FROM visit v
                       JOIN museum m2 ON v.museum_id = m2.museum_id
                       JOIN item i2 ON m2.museum_id = i2.museum_id
                       WHERE v.guest_id = ?
                   )
                   GROUP BY m.museum_id
                   ORDER BY item_count DESC
                   LIMIT 5""",
                (guest_id, guest_id)
            )
            return cur.fetchall()

class MaintenanceService:
    """Business logic for maintenance/upkeep operations."""

    @staticmethod
    def schedule_maintenance(item_id: int, task: str, done_on: str,
                           technician: str, cost: Optional[float],
                           user_role: str, user_id: int) -> None:
        """Schedule maintenance with business validation."""
        AuthorizationManager.require_permission(user_role, 'update')

        item_id = InputValidator.validate_positive_int(item_id, "Item ID")
        task = InputValidator.validate_name(task, "Task description")
        done_on = InputValidator.validate_date(done_on)
        technician = InputValidator.validate_name(technician, "Technician name")

        # Business rule: Maintenance cost must be reasonable
        if cost is not None:
            if cost < 0:
                raise ValidationError("Maintenance cost cannot be negative")
            if cost > 100000:
                # High-cost maintenance requires admin approval
                AuthorizationManager.require_role(user_role, 'curator')

        repos.MaintenanceRepository.schedule(item_id, task, done_on, technician)
        AuditLogger.log_action(
            user_id, 'CREATE', 'upkeep', None, None,
            f"item_id={item_id},task={task},cost={cost}"
        )

    @staticmethod
    def get_maintenance_schedule(days_ahead: int = 30) -> List[Dict]:
        """Get upcoming maintenance in the next N days."""
        from .connection import get_cursor
        future_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

        with get_cursor() as cur:
            cur.execute(
                """SELECT * FROM item_maintenance_view
                   WHERE done_on BETWEEN date('now') AND ?
                   ORDER BY done_on""",
                (future_date,)
            )
            return cur.fetchall()

    @staticmethod
    def get_items_needing_maintenance(months_since_last: int = 6) -> List[Dict]:
        """Identify items that haven't been maintained recently."""
        from .connection import get_cursor
        cutoff_date = (datetime.now() - timedelta(days=months_since_last*30)).strftime('%Y-%m-%d')

        with get_cursor() as cur:
            cur.execute(
                """SELECT i.item_id, i.title, i.category, m.name as museum_name,
                   MAX(u.done_on) as last_maintenance
                   FROM item i
                   JOIN museum m ON i.museum_id = m.museum_id
                   LEFT JOIN upkeep u ON i.item_id = u.item_id
                   WHERE i.status = 'active'
                   GROUP BY i.item_id
                   HAVING last_maintenance IS NULL OR last_maintenance < ?
                   ORDER BY last_maintenance ASC NULLS FIRST""",
                (cutoff_date,)
            )
            return cur.fetchall()

    @staticmethod
    def get_maintenance_cost_analysis(start_date: str, end_date: str) -> Dict:
        """Analyze maintenance costs over a period."""
        from .connection import get_cursor
        with get_cursor() as cur:
            cur.execute(
                """SELECT
                   COUNT(*) as total_tasks,
                   SUM(COALESCE(cost, 0)) as total_cost,
                   AVG(COALESCE(cost, 0)) as avg_cost,
                   MIN(cost) as min_cost,
                   MAX(cost) as max_cost
                   FROM upkeep
                   WHERE done_on BETWEEN ? AND ?""",
                (start_date, end_date)
            )
            return cur.fetchone()

class ReportingService:
    """Business logic for generating reports and analytics."""

    @staticmethod
    def generate_museum_performance_report(museum_id: int) -> Dict:
        """Generate comprehensive performance report for a museum."""
        from .connection import get_cursor
        with get_cursor() as cur:
            # Get basic stats
            cur.execute("SELECT * FROM museum_stats WHERE museum_id = ?", (museum_id,))
            stats = cur.fetchone()

            # Get visitor trends (last 12 months)
            cur.execute(
                """SELECT strftime('%Y-%m', visited_on) as month, COUNT(*) as visits
                   FROM visit
                   WHERE museum_id = ?
                   AND visited_on >= date('now', '-12 months')
                   GROUP BY month
                   ORDER BY month""",
                (museum_id,)
            )
            visitor_trends = cur.fetchall()

            # Get top categories
            cur.execute(
                """SELECT category, COUNT(*) as count
                   FROM item
                   WHERE museum_id = ?
                   GROUP BY category
                   ORDER BY count DESC
                   LIMIT 5""",
                (museum_id,)
            )
            top_categories = cur.fetchall()

            return {
                'stats': dict(stats) if stats else {},
                'visitor_trends': [dict(row) for row in visitor_trends],
                'top_categories': [dict(row) for row in top_categories]
            }

    @staticmethod
    def generate_executive_summary() -> Dict:
        """Generate executive summary across all museums."""
        from .connection import get_cursor
        with get_cursor() as cur:
            # Get summary counts from individual tables
            cur.execute("SELECT COUNT(*) as total_museums FROM museum")
            museums = cur.fetchone()

            cur.execute("SELECT COUNT(*) as total_items FROM item")
            items = cur.fetchone()

            cur.execute("SELECT COUNT(*) as total_visitors FROM guest")
            visitors = cur.fetchone()

            cur.execute(
                """SELECT COUNT(*) as visits_last_month
                FROM visit
                WHERE visited_on >= date('now', '-1 month')"""
            )
            recent_visits = cur.fetchone()

            return {
                'summary': {
                    'total_museums': museums['total_museums'] if museums else 0,
                    'total_items': items['total_items'] if items else 0,
                    'total_visitors': visitors['total_visitors'] if visitors else 0
                },
                'recent_activity': dict(recent_visits) if recent_visits else {}
            }


