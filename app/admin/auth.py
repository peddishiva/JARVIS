"""Admin authentication, password hashing, and session management for JARVIS."""

from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_connection


def _resolve_db_path(db_path=None):
    if db_path is not None:
        return db_path
    try:
        from flask import current_app
        if current_app and current_app.config.get("DB_PATH"):
            return current_app.config["DB_PATH"]
    except Exception:
        pass
    return None


def admin_exists(db_path=None):
    """Check if any active admin account exists in the database."""
    db_path = _resolve_db_path(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM admin_user WHERE is_active = 1 LIMIT 1")
        return cursor.fetchone() is not None
    finally:
        conn.close()


def create_admin_user(username, password, db_path=None):
    """Create a new admin user with a securely hashed password.

    Returns (success: bool, error_message: str | None).
    """
    username = str(username).strip()
    if not username:
        return False, "Username is required."
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."

    password_hash = generate_password_hash(password, method="scrypt")

    db_path = _resolve_db_path(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM admin_user WHERE LOWER(username) = ?", (username.lower(),))
        if cursor.fetchone() is not None:
            return False, "An account with that username already exists."

        cursor.execute(
            "INSERT INTO admin_user (username, password_hash, is_active) VALUES (?, ?, 1)",
            (username, password_hash),
        )
        conn.commit()
        return True, None
    except Exception as e:
        return False, f"Database error creating admin: {e}"
    finally:
        conn.close()


def authenticate_admin(username, password, db_path=None):
    """Authenticate an admin user.

    Returns admin user dict if valid, or None.
    """
    username = str(username).strip()
    if not username or not password:
        return None

    db_path = _resolve_db_path(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, is_active FROM admin_user WHERE LOWER(username) = ?",
            (username.lower(),),
        )
        row = cursor.fetchone()
        if not row:
            return None

        admin_id, db_username, db_hash, is_active = row
        if not is_active:
            return None

        if check_password_hash(db_hash, password):
            return {
                "id": admin_id,
                "username": db_username,
                "is_active": bool(is_active),
            }
        return None
    finally:
        conn.close()


def get_admin_by_id(admin_id, db_path=None):
    """Retrieve an active admin user record by ID."""
    if not admin_id:
        return None

    db_path = _resolve_db_path(db_path)
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, is_active FROM admin_user WHERE id = ?",
            (admin_id,),
        )
        row = cursor.fetchone()
        if row and row[2]:
            return {"id": row[0], "username": row[1], "is_active": bool(row[2])}
        return None
    finally:
        conn.close()


def login_required(f):
    """Decorator to protect administrative views against unauthenticated access and inactive accounts."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if system has any admin accounts configured
        if not admin_exists():
            if request.is_json or request.path.startswith("/admin/api/"):
                return jsonify({"error": "Admin setup required", "setup_required": True}), 403
            return redirect(url_for("admin.setup"))

        admin_id = session.get("admin_id")
        if not admin_id:
            if request.is_json or request.path.startswith("/admin/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("admin.login", next=request.path))

        # Revalidate that the admin account still exists and remains active in SQLite
        admin_user = get_admin_by_id(admin_id)
        if not admin_user or not admin_user.get("is_active"):
            session.clear()
            if request.is_json or request.path.startswith("/admin/api/"):
                return jsonify({"error": "Authentication required or account deactivated"}), 401
            return redirect(url_for("admin.login", next=request.path))

        return f(*args, **kwargs)

    return decorated_function
