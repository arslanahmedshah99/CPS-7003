"""
Security module for authentication, authorization, and input validation.
Implements role-based access control (RBAC) and secure password handling.
"""
import hashlib
import secrets
import re
from datetime import datetime
from typing import Optional, Dict, Any
from .connection import get_cursor

# Role hierarchy: admin > curator > staff > viewer
ROLES = {
    'admin': 4,
    'curator': 3,
    'staff': 2,
    'viewer': 1
}

PERMISSIONS = {
    'admin': ['create', 'read', 'update', 'delete', 'manage_users'],
    'curator': ['create', 'read', 'update', 'manage_exhibits'],
    'staff': ['read', 'update', 'create_visits'],
    'viewer': ['read']
}

class SecurityException(Exception):
    """Custom exception for security-related errors."""
    pass

class AuthenticationError(SecurityException):
    """Raised when authentication fails."""
    pass

class AuthorizationError(SecurityException):
    """Raised when user lacks permissions."""
    pass

class ValidationError(SecurityException):
    """Raised when input validation fails."""
    pass

def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a random salt."""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, pwd_hash = stored_hash.split('$')
        return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
    except (ValueError, AttributeError):
        return False

class InputValidator:
    """Validates user inputs to prevent SQL injection and malformed data."""

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format."""
        email = email.strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError(f"Invalid email format: {email}")
        return email

    @staticmethod
    def validate_name(name: str, field_name: str = "Name") -> str:
        """Validate name fields (non-empty, reasonable length)."""
        name = name.strip()
        if not name or len(name) < 2:
            raise ValidationError(f"{field_name} must be at least 2 characters")
        if len(name) > 100:
            raise ValidationError(f"{field_name} must be less than 100 characters")
        return name

    @staticmethod
    def validate_date(date_str: str) -> str:
        """Validate date format (YYYY-MM-DD)."""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            raise ValidationError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

    @staticmethod
    def validate_positive_int(value: Any, field_name: str = "Value") -> int:
        """Validate positive integer."""
        try:
            val = int(value)
            if val <= 0:
                raise ValidationError(f"{field_name} must be positive")
            return val
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid integer")

    @staticmethod
    def validate_role(role: str) -> str:
        """Validate user role."""
        if role not in ROLES:
            raise ValidationError(f"Invalid role: {role}. Must be one of {list(ROLES.keys())}")
        return role

    @staticmethod
    def sanitize_string(text: str, max_length: int = 500) -> str:
        """Sanitize text input."""
        text = text.strip()
        if len(text) > max_length:
            raise ValidationError(f"Text exceeds maximum length of {max_length} characters")
        # Remove potentially dangerous characters
        text = re.sub(r'[<>{}]', '', text)
        return text

class AuthenticationManager:
    """Manages user authentication and session handling."""

    @staticmethod
    def create_user(username: str, password: str, email: str, role: str = 'viewer') -> int:
        """Create a new user with hashed password."""
        username = InputValidator.validate_name(username, "Username")
        email = InputValidator.validate_email(email)
        role = InputValidator.validate_role(role)

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")

        password_hash = hash_password(password)

        with get_cursor(commit=True) as cur:
            try:
                cur.execute(
                    "INSERT INTO user(username, password_hash, email, role) VALUES (?, ?, ?, ?)",
                    (username, password_hash, email, role)
                )
                return cur.lastrowid
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    raise ValidationError("Username or email already exists")
                raise

    @staticmethod
    def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user and return user info if successful."""
        with get_cursor() as cur:
            cur.execute(
                "SELECT user_id, username, password_hash, role, email, is_active FROM user WHERE username = ?",
                (username,)
            )
            user = cur.fetchone()

            if not user:
                raise AuthenticationError("Invalid username or password")

            if not user['is_active']:
                raise AuthenticationError("Account is disabled")

            if not verify_password(password, user['password_hash']):
                raise AuthenticationError("Invalid username or password")

            # Update last login
            cur.execute(
                "UPDATE user SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user['user_id'],)
            )

            return {
                'user_id': user['user_id'],
                'username': user['username'],
                'role': user['role'],
                'email': user['email']
            }

    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> None:
        """Change user password."""
        with get_cursor(commit=True) as cur:
            cur.execute("SELECT password_hash FROM user WHERE user_id = ?", (user_id,))
            user = cur.fetchone()

            if not user or not verify_password(old_password, user['password_hash']):
                raise AuthenticationError("Current password is incorrect")

            if len(new_password) < 8:
                raise ValidationError("New password must be at least 8 characters")

            new_hash = hash_password(new_password)
            cur.execute(
                "UPDATE user SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (new_hash, user_id)
            )

class AuthorizationManager:
    """Manages role-based access control."""

    @staticmethod
    def check_permission(user_role: str, required_permission: str) -> bool:
        """Check if a user role has a specific permission."""
        return required_permission in PERMISSIONS.get(user_role, [])

    @staticmethod
    def require_permission(user_role: str, required_permission: str) -> None:
        """Raise an exception if user lacks required permission."""
        if not AuthorizationManager.check_permission(user_role, required_permission):
            raise AuthorizationError(
                f"Permission denied. Required: {required_permission}, User role: {user_role}"
            )

    @staticmethod
    def require_role(user_role: str, minimum_role: str) -> None:
        """Require user to have at least the specified role level."""
        if ROLES.get(user_role, 0) < ROLES.get(minimum_role, 0):
            raise AuthorizationError(
                f"Insufficient privileges. Required: {minimum_role}, User role: {user_role}"
            )

class AuditLogger:
    """Logs security-relevant actions for compliance and monitoring."""

    @staticmethod
    def log_action(user_id: Optional[int], action: str, table_name: str,
                   record_id: Optional[int] = None, old_values: Optional[str] = None,
                   new_values: Optional[str] = None, ip_address: Optional[str] = None) -> None:
        """Log an action to the audit log."""
        with get_cursor(commit=True) as cur:
            cur.execute(
                """INSERT INTO audit_log(user_id, action, table_name, record_id, old_values, new_values, ip_address)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, action, table_name, record_id, old_values, new_values, ip_address)
            )

    @staticmethod
    def get_user_activity(user_id: int, limit: int = 50):
        """Get recent activity for a specific user."""
        with get_cursor() as cur:
            cur.execute(
                """SELECT * FROM audit_log
                   WHERE user_id = ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (user_id, limit)
            )
            return cur.fetchall()

    @staticmethod
    def get_table_changes(table_name: str, limit: int = 100):
        """Get recent changes to a specific table."""
        with get_cursor() as cur:
            cur.execute(
                """SELECT * FROM audit_log
                   WHERE table_name = ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (table_name, limit)
            )
            return cur.fetchall()

