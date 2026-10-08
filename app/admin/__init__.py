"""JARVIS Admin Dashboard package."""

from app.admin.server import create_app, run_admin_server
from app.admin.auth import (
    admin_exists,
    create_admin_user,
    authenticate_admin,
    login_required,
)
from app.admin.csrf import generate_csrf_token, validate_csrf_token
from app.admin.services import (
    ContactsRepository,
    WebCommandsRepository,
    SystemCommandsRepository,
    DashboardService,
)

__all__ = [
    "create_app",
    "run_admin_server",
    "admin_exists",
    "create_admin_user",
    "authenticate_admin",
    "login_required",
    "generate_csrf_token",
    "validate_csrf_token",
    "ContactsRepository",
    "WebCommandsRepository",
    "SystemCommandsRepository",
    "DashboardService",
]
