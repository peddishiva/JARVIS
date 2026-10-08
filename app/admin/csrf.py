"""CSRF protection mechanisms for the JARVIS Admin Dashboard."""

import hmac
import secrets
from flask import session, request, jsonify, abort

CSRF_SESSION_KEY = "_csrf_token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def generate_csrf_token():
    """Retrieve existing CSRF token from session or generate a new cryptographically secure token."""
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_hex(32)
        session[CSRF_SESSION_KEY] = token
    return token


def validate_csrf_token(token):
    """Validate a submitted CSRF token against the session token using constant-time comparison."""
    if not token:
        return False
    session_token = session.get(CSRF_SESSION_KEY)
    if not session_token:
        return False
    return hmac.compare_digest(str(session_token), str(token))


def verify_csrf():
    """Verify CSRF token on mutating HTTP requests.
    
    Returns None if valid, or returns a 403 response if invalid or missing.
    """
    if request.method in SAFE_METHODS:
        return None

    submitted_token = (
        request.headers.get("X-CSRF-Token")
        or request.headers.get("X-CSRFToken")
        or request.form.get("csrf_token")
    )
    if not submitted_token and request.is_json:
        submitted_token = (request.get_json(silent=True) or {}).get("csrf_token")

    if not submitted_token or not validate_csrf_token(submitted_token):
        if request.is_json or request.path.startswith("/admin/api/"):
            return jsonify({"error": "Invalid or missing CSRF token"}), 403
        abort(403, description="Forbidden: CSRF token missing or invalid.")
