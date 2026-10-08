"""Input validation routines for the JARVIS Admin Dashboard."""

import re
from urllib.parse import urlparse

# Disallowed dangerous URL schemes
DANGEROUS_URL_SCHEMES = {"javascript", "data", "file", "vbscript", "about"}

# Disallowed shell metacharacters for system command paths
DANGEROUS_SHELL_PATTERN = re.compile(r"[;&|><`$\r\n]")

# Basic email validation regex
EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$")

# Phone number validation regex (digits, optional leading +, optional spaces/dashes)
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-]{7,25}$")


def validate_admin_credentials(username, password):
    """Validate admin username and password input."""
    username = str(username or "").strip()
    if not username:
        return False, "Username is required."
    if len(username) < 3 or len(username) > 50:
        return False, "Username must be between 3 and 50 characters."
    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", username):
        return False, "Username may only contain letters, numbers, hyphens, and underscores."

    if not password:
        return False, "Password is required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."

    return True, None


def validate_contact(name, mobile_no, email=None):
    """Validate contact form inputs.

    Returns (is_valid: bool, error_message: str | None).
    """
    name = str(name or "").strip()
    if not name:
        return False, "Contact name is required."
    if len(name) > 100:
        return False, "Contact name cannot exceed 100 characters."

    mobile_no = str(mobile_no or "").strip()
    if not mobile_no:
        return False, "Mobile number is required."
    if not PHONE_REGEX.match(mobile_no):
        return False, "Please enter a valid phone number (7 to 25 digits, optional + prefix)."

    if email:
        email = str(email).strip()
        if len(email) > 120:
            return False, "Email address cannot exceed 120 characters."
        if not EMAIL_REGEX.match(email):
            return False, "Please enter a valid email address."

    return True, None


def validate_web_command(name, url):
    """Validate web shortcut command inputs.

    Returns (is_valid: bool, error_message: str | None).
    """
    name = str(name or "").strip()
    if not name:
        return False, "Command name is required."
    if len(name) > 100:
        return False, "Command name cannot exceed 100 characters."

    url = str(url or "").strip()
    if not url:
        return False, "URL is required."
    if len(url) > 1000:
        return False, "URL cannot exceed 1000 characters."

    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if not scheme:
            return False, "URL must include http:// or https:// protocol scheme."
        if scheme in DANGEROUS_URL_SCHEMES:
            return False, f"URL scheme '{scheme}:' is blocked for security reasons."
        if scheme not in ("http", "https"):
            return False, f"Only http:// and https:// URLs are allowed (got '{scheme}:')."
        if not parsed.netloc:
            return False, "URL must contain a valid domain name."
    except Exception:
        return False, "Invalid URL format."

    return True, None


def validate_system_command(name, path):
    """Validate system application command inputs.

    Returns (is_valid: bool, error_message: str | None).
    """
    name = str(name or "").strip()
    if not name:
        return False, "Command name is required."
    if len(name) > 100:
        return False, "Command name cannot exceed 100 characters."

    path = str(path or "").strip()
    if not path:
        return False, "Application path is required."
    if len(path) > 1000:
        return False, "Path cannot exceed 1000 characters."

    if DANGEROUS_SHELL_PATTERN.search(path):
        return False, "Path cannot contain shell metacharacters (; & | > < ` $ or newlines)."

    return True, None
