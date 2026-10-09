"""Automated test suite for JARVIS Phase 5 Admin Dashboard.

Covers:
- Authentication & First-Run Setup
- Session Security & Inactive Account Revocation
- CSRF Protection (Forms & API Mutations)
- Open Redirect Prevention
- Authorization Enforcement
- Contacts CRUD & SQL Injection Defense
- Web Commands CRUD & URL Scheme Rejection
- System Commands CRUD & Command Injection Rejection
- Architecture Rules (app -> engine = 0)
"""

import os
import sys
import glob
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import init_db, get_connection
from app.admin.server import create_app
from app.admin.auth import (
    admin_exists,
    create_admin_user,
    authenticate_admin,
    get_admin_by_id,
)
from app.admin.csrf import CSRF_SESSION_KEY
from app.admin.routes import is_safe_redirect_url
from app.admin.validators import (
    validate_admin_credentials,
    validate_contact,
    validate_web_command,
    validate_system_command,
)
from app.admin.services import (
    ContactsRepository,
    WebCommandsRepository,
    SystemCommandsRepository,
    DashboardService,
)
from app.services.whatsapp import find_contact
from app.services.system import open_command


class TestPhase5Admin(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_jarvis.db")
        init_db(self.db_path)

        # Create isolated test Flask app
        self.app = create_app(
            secret_key="test-secure-key",
            test_config={"TESTING": True, "DB_PATH": self.db_path},
        )
        self.client = self.app.test_client()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _get_csrf_token(self):
        """Helper to retrieve CSRF token by initializing a session via GET /admin/login."""
        with self.client:
            self.client.get("/admin/login")
            from flask import session
            return session.get(CSRF_SESSION_KEY)

    def _login_admin(self, username="admin", password="AdminPassword123!"):
        """Helper to create admin user and log in via test client with valid CSRF token."""
        create_admin_user(username, password, self.db_path)
        token = self._get_csrf_token()
        resp = self.client.post(
            "/admin/login",
            data={"username": username, "password": password, "csrf_token": token},
            follow_redirects=False,
        )
        return resp

    # ============================================================
    # 1. AUTHENTICATION & SETUP
    # ============================================================

    def test_first_run_setup_and_hashing(self):
        """Verify first run setup redirects to setup, creates admin with scrypt hash, and rejects duplicate."""
        self.assertFalse(admin_exists(self.db_path))

        # Accessing dashboard before setup redirects to setup
        resp = self.client.get("/admin/dashboard", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/setup", resp.headers["Location"])

        # Create first admin user
        ok, err = create_admin_user("admin_shiva", "SecurePass123!", self.db_path)
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertTrue(admin_exists(self.db_path))

        # Verify password hash format (scrypt) and not plaintext
        conn = get_connection(self.db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT password_hash FROM admin_user WHERE username = 'admin_shiva'")
            row = cur.fetchone()
            self.assertIsNotNone(row)
            pw_hash = row[0]
            self.assertNotEqual(pw_hash, "SecurePass123!")
            self.assertTrue(pw_hash.startswith("scrypt:"))
        finally:
            conn.close()

        # Reject duplicate username (case-insensitive)
        dup_ok, dup_err = create_admin_user("ADMIN_SHIVA", "AnotherPass123!", self.db_path)
        self.assertFalse(dup_ok)
        self.assertIn("already exists", dup_err.lower())

        # Setup route is now blocked and redirects to login
        setup_resp = self.client.get("/admin/setup", follow_redirects=False)
        self.assertEqual(setup_resp.status_code, 302)
        self.assertIn("/admin/login", setup_resp.headers["Location"])

    def test_authentication_credential_validation(self):
        """Verify authentication validates passwords, fails on bad password or nonexistent user."""
        create_admin_user("admin", "MyPassword123!", self.db_path)

        # Successful auth
        user = authenticate_admin("admin", "MyPassword123!", self.db_path)
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "admin")

        # Wrong password
        wrong = authenticate_admin("admin", "WrongPass123!", self.db_path)
        self.assertIsNone(wrong)

        # Nonexistent user
        missing = authenticate_admin("nobody", "MyPassword123!", self.db_path)
        self.assertIsNone(missing)

        # Short password validation
        valid, msg = validate_admin_credentials("admin", "short")
        self.assertFalse(valid)
        self.assertIn("at least 8 characters", msg)

    # ============================================================
    # 2. SESSION SECURITY & INACTIVE ACCOUNT REVOCATION
    # ============================================================

    def test_session_cookie_security_and_inactive_revocation(self):
        """Verify HttpOnly, SameSite=Lax, and immediate session revocation if account becomes inactive."""
        self.assertTrue(self.app.config["SESSION_COOKIE_HTTPONLY"])
        self.assertEqual(self.app.config["SESSION_COOKIE_SAMESITE"], "Lax")

        # Create second admin so admin_exists remains True when admin is deactivated
        create_admin_user("admin2", "AdminPass222!", self.db_path)
        # Log in
        self._login_admin("admin", "AdminPass123!")

        # Request to dashboard succeeds while active
        with self.client:
            dash = self.client.get("/admin/dashboard")
            self.assertEqual(dash.status_code, 200)

            # Deactivate admin account directly in database
            conn = get_connection(self.db_path)
            try:
                conn.cursor().execute("UPDATE admin_user SET is_active = 0 WHERE username = 'admin'")
                conn.commit()
            finally:
                conn.close()

            # Next request to protected route must revoke session and redirect to login
            revoked_resp = self.client.get("/admin/dashboard", follow_redirects=False)
            self.assertEqual(revoked_resp.status_code, 302)
            self.assertIn("/admin/login", revoked_resp.headers["Location"])

            # Verify session was cleared
            from flask import session
            self.assertIsNone(session.get("admin_id"))

    # ============================================================
    # 3. CSRF PROTECTION & SAFE LOGOUT
    # ============================================================

    def test_csrf_protection_on_html_forms(self):
        """Verify mutating HTML forms reject missing or invalid CSRF tokens with 403."""
        self._login_admin("admin", "AdminPass123!")

        # 1. Missing CSRF token -> 403 Forbidden
        resp_no_csrf = self.client.post(
            "/admin/contacts/create",
            data={"name": "Alice", "mobile_no": "+919876543210"},
        )
        self.assertEqual(resp_no_csrf.status_code, 403)

        # 2. Invalid CSRF token -> 403 Forbidden
        resp_bad_csrf = self.client.post(
            "/admin/contacts/create",
            data={"name": "Alice", "mobile_no": "+919876543210", "csrf_token": "bad_token_123"},
        )
        self.assertEqual(resp_bad_csrf.status_code, 403)

        # 3. Valid CSRF token -> 302 redirect (success)
        token = self._get_csrf_token()
        resp_valid = self.client.post(
            "/admin/contacts/create",
            data={"name": "Alice", "mobile_no": "+919876543210", "csrf_token": token},
            follow_redirects=False,
        )
        self.assertEqual(resp_valid.status_code, 302)
        self.assertIn("/admin/contacts", resp_valid.headers["Location"])

    def test_csrf_protection_on_api_mutations(self):
        """Verify API mutations require X-CSRF-Token and reject invalid tokens with 403 JSON."""
        self._login_admin("admin", "AdminPass123!")

        # Missing token -> 403 JSON
        resp_no_token = self.client.post(
            "/admin/api/contacts",
            json={"name": "Bob", "mobile_no": "+919876543211"},
        )
        self.assertEqual(resp_no_token.status_code, 403)
        self.assertIn("error", resp_no_token.get_json())

        # Valid token via header -> 201 Created
        token = self._get_csrf_token()
        resp_valid = self.client.post(
            "/admin/api/contacts",
            json={"name": "Bob", "mobile_no": "+919876543211"},
            headers={"X-CSRF-Token": token},
        )
        self.assertEqual(resp_valid.status_code, 201)

    def test_logout_post_only_and_csrf_protected(self):
        """Verify logout rejects GET with 405, rejects POST without CSRF with 403, and succeeds with valid CSRF."""
        self._login_admin("admin", "AdminPass123!")

        # GET /admin/logout -> 405 Method Not Allowed
        get_logout = self.client.get("/admin/logout")
        self.assertEqual(get_logout.status_code, 405)

        # POST without CSRF -> 403 Forbidden
        no_csrf_logout = self.client.post("/admin/logout")
        self.assertEqual(no_csrf_logout.status_code, 403)

        # POST with CSRF -> 302 Redirect to login
        token = self._get_csrf_token()
        valid_logout = self.client.post(
            "/admin/logout",
            data={"csrf_token": token},
            follow_redirects=False,
        )
        self.assertEqual(valid_logout.status_code, 302)
        self.assertIn("/admin/login", valid_logout.headers["Location"])

    # ============================================================
    # 4. OPEN REDIRECT DEFENSE
    # ============================================================

    def test_open_redirect_defense(self):
        """Verify is_safe_redirect_url and login ?next= parameter prevent external redirects."""
        # Unit checks on validator
        self.assertTrue(is_safe_redirect_url("/admin/dashboard"))
        self.assertTrue(is_safe_redirect_url("/admin/contacts"))
        self.assertFalse(is_safe_redirect_url("https://attacker.com"))
        self.assertFalse(is_safe_redirect_url("http://attacker.com/evil"))
        self.assertFalse(is_safe_redirect_url("//attacker.com"))
        self.assertFalse(is_safe_redirect_url("\\\\attacker.com"))
        self.assertFalse(is_safe_redirect_url("/\\attacker.com"))
        self.assertFalse(is_safe_redirect_url("javascript:alert(1)"))
        self.assertFalse(is_safe_redirect_url("data:text/html,evil"))
        self.assertFalse(is_safe_redirect_url(""))

        create_admin_user("admin", "AdminPass123!", self.db_path)

        # Login with malicious next parameter falls back to dashboard
        token = self._get_csrf_token()
        resp_malicious = self.client.post(
            "/admin/login?next=https://attacker.com/steal-creds",
            data={"username": "admin", "password": "AdminPass123!", "csrf_token": token},
            follow_redirects=False,
        )
        self.assertEqual(resp_malicious.status_code, 302)
        # Clear session before next login attempt
        with self.client.session_transaction() as sess:
            sess.clear()

        # Login with safe next parameter is honored
        token2 = self._get_csrf_token()
        resp_safe = self.client.post(
            "/admin/login?next=/admin/web-commands",
            data={"username": "admin", "password": "AdminPass123!", "csrf_token": token2},
            follow_redirects=False,
        )
        self.assertEqual(resp_safe.status_code, 302)
        self.assertIn("/admin/web-commands", resp_safe.headers["Location"])

    # ============================================================
    # 5. AUTHORIZATION ENFORCEMENT
    # ============================================================

    def test_unauthenticated_access_rejected(self):
        """Verify all protected HTML views redirect to login and API endpoints return 401."""
        create_admin_user("admin", "AdminPass123!", self.db_path)

        # Unauthenticated HTML views
        for path in ["/admin/dashboard", "/admin/contacts", "/admin/web-commands", "/admin/system-commands"]:
            resp = self.client.get(path, follow_redirects=False)
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/admin/login", resp.headers["Location"])

        # Unauthenticated API views
        for api_path in ["/admin/api/summary", "/admin/api/contacts", "/admin/api/web-commands", "/admin/api/system-commands"]:
            resp = self.client.get(api_path)
            self.assertEqual(resp.status_code, 401)
            self.assertTrue(resp.is_json)

    # ============================================================
    # 6. CONTACTS CRUD & SQL INJECTION DEFENSE
    # ============================================================

    def test_contacts_crud_and_validation(self):
        """Verify contacts CRUD, phone/email validation, and parameterized SQL injection defense."""
        # Validation
        v1, _ = validate_contact("", "+919876543210")
        self.assertFalse(v1)
        v2, _ = validate_contact("User", "invalid_phone")
        self.assertFalse(v2)
        v3, _ = validate_contact("User", "+919876543210", "bad_email")
        self.assertFalse(v3)

        # Create
        ok, _ = ContactsRepository.create("Charlie", "+919876543210", "charlie@example.com", self.db_path)
        self.assertTrue(ok)

        # Read & Search
        items = ContactsRepository.search("charlie", self.db_path)
        self.assertEqual(len(items), 1)
        c = items[0]
        self.assertEqual(c["name"], "Charlie")
        self.assertEqual(c["mobile_no"], "+919876543210")

        # WhatsApp assistant integration reads updated record
        mobile, _ = find_contact("send message to Charlie", db_path=self.db_path)
        self.assertEqual(mobile, "+919876543210")

        # Update
        up_ok, _ = ContactsRepository.update(c["id"], "Charlie Brown", "+919876543299", None, self.db_path)
        self.assertTrue(up_ok)
        updated = ContactsRepository.get_by_id(c["id"], self.db_path)
        self.assertEqual(updated["name"], "Charlie Brown")
        self.assertEqual(updated["mobile_no"], "+919876543299")

        # SQL injection attack string handled safely
        sqli_name = "Robert'); DROP TABLE contacts;--"
        sqli_ok, _ = ContactsRepository.create(sqli_name, "+919876543210", None, self.db_path)
        self.assertTrue(sqli_ok)
        sqli_res = ContactsRepository.search("Robert", self.db_path)
        self.assertEqual(len(sqli_res), 1)
        self.assertEqual(sqli_res[0]["name"], sqli_name)

        # Delete
        del_ok, _ = ContactsRepository.delete(c["id"], self.db_path)
        self.assertTrue(del_ok)
        self.assertIsNone(ContactsRepository.get_by_id(c["id"], self.db_path))

    # ============================================================
    # 7. WEB COMMANDS CRUD & URL SCHEME REJECTION
    # ============================================================

    def test_web_commands_crud_and_url_security(self):
        """Verify web commands CRUD and rejection of dangerous URL schemes."""
        dangerous_urls = [
            "javascript:alert('pwned')",
            "data:text/html,<script>alert(1)</script>",
            "file:///etc/passwd",
            "vbscript:msgbox(1)",
            "about:blank",
            "ftp://files.example.com",
            "not_a_valid_url",
            "//protocol-relative.com",
        ]
        for bad_url in dangerous_urls:
            valid, err = validate_web_command("test", bad_url)
            self.assertFalse(valid, f"Failed to reject dangerous URL: {bad_url}")

        # Valid create
        ok, _ = WebCommandsRepository.create("docs", "https://docs.python.org/3/", self.db_path)
        self.assertTrue(ok)

        # Search
        res = WebCommandsRepository.search("docs", self.db_path)
        self.assertEqual(len(res), 1)
        w = res[0]
        self.assertEqual(w["url"], "https://docs.python.org/3/")

        # Assistant launcher integration opens configured URL
        opened = []
        open_command("open docs", speak_fn=lambda t: opened.append(t), db_path=self.db_path)
        self.assertTrue(any("Opening" in o for o in opened))

        # Delete
        del_ok, _ = WebCommandsRepository.delete(w["id"], self.db_path)
        self.assertTrue(del_ok)
        self.assertIsNone(WebCommandsRepository.get_by_id(w["id"], self.db_path))

    # ============================================================
    # 8. SYSTEM COMMANDS CRUD & METALOGICAL SAFETY
    # ============================================================

    def test_system_commands_crud_and_metacharacter_rejection(self):
        """Verify system commands reject shell metacharacters and execute safely."""
        dangerous_paths = [
            "notepad & calc",
            "calc | dir",
            "; echo hack",
            "app.exe > output.txt",
            "tool.exe `id`",
            "prog.exe $VAR",
            "app.exe\nmalicious",
        ]
        for bad_path in dangerous_paths:
            valid, err = validate_system_command("app", bad_path)
            self.assertFalse(valid, f"Failed to reject dangerous shell path: {bad_path}")

        # Valid creation
        ok, _ = SystemCommandsRepository.create("editor", "notepad.exe", self.db_path)
        self.assertTrue(ok)

        items = SystemCommandsRepository.search("editor", self.db_path)
        self.assertEqual(len(items), 1)
        cmd = items[0]
        self.assertEqual(cmd["path"], "notepad.exe")

        # Test launch route with mocked os.startfile
        with patch("os.startfile", return_value=None) as mock_start:
            launch_ok, launch_msg = SystemCommandsRepository.test_launch(cmd["id"], self.db_path)
            self.assertTrue(launch_ok)
            mock_start.assert_called_once_with("notepad.exe")

        # Delete
        del_ok, _ = SystemCommandsRepository.delete(cmd["id"], self.db_path)
        self.assertTrue(del_ok)
        self.assertIsNone(SystemCommandsRepository.get_by_id(cmd["id"], self.db_path))

    # ============================================================
    # 9. ARCHITECTURAL INTEGRITY AUDIT
    # ============================================================

    def test_architecture_app_never_imports_engine(self):
        """Verify zero 'import engine' or 'from engine' references in app/ package."""
        for pyfile in glob.glob("app/**/*.py", recursive=True):
            with open(pyfile, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertNotIn("import engine", content, f"Forbidden engine import in {pyfile}")
                self.assertNotIn("from engine", content, f"Forbidden engine import in {pyfile}")
                if "app/admin" in pyfile.replace("\\", "/"):
                    self.assertNotIn("shell=True", content, f"Forbidden shell=True in {pyfile}")

    # ============================================================
    # 10. ADMIN DASHBOARD LAUNCHER & AVAILABILITY AUDIT
    # ============================================================

    def test_open_admin_dashboard_when_server_running(self):
        """Verify open_admin_dashboard invokes browser with exact admin URL when server is active."""
        from app.config import ADMIN_HOST, ADMIN_PORT
        from app.admin import open_admin_dashboard

        expected_url = f"http://{ADMIN_HOST}:{ADMIN_PORT}/admin"
        mock_browser = MagicMock()

        with patch("app.admin.server.is_admin_server_running", return_value=True):
            res = open_admin_dashboard(browser_fn=mock_browser)
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["url"], expected_url)
            mock_browser.assert_called_once_with(expected_url)

    def test_open_admin_dashboard_when_server_unavailable(self):
        """Verify open_admin_dashboard returns non-blocking error and does not open browser when down."""
        from app.config import ADMIN_HOST, ADMIN_PORT
        from app.admin import open_admin_dashboard

        mock_browser = MagicMock()

        with patch("app.admin.server.is_admin_server_running", return_value=False):
            res = open_admin_dashboard(browser_fn=mock_browser)
            self.assertEqual(res["status"], "error")
            self.assertIn("Admin Dashboard is not running", res["message"])
            self.assertIn(f"http://{ADMIN_HOST}:{ADMIN_PORT}/admin", res["message"])
            mock_browser.assert_not_called()

    def test_open_admin_dashboard_browser_exception(self):
        """Verify graceful error handling if browser launcher throws an exception."""
        from app.admin import open_admin_dashboard

        mock_browser = MagicMock(side_effect=RuntimeError("Browser launch failed"))

        with patch("app.admin.server.is_admin_server_running", return_value=True):
            res = open_admin_dashboard(browser_fn=mock_browser)
            self.assertEqual(res["status"], "error")
            self.assertIn("Could not launch browser", res["message"])

    def test_eel_exposed_open_admin_dashboard_delegation(self):
        """Verify engine.features.openAdminDashboard correctly delegates to open_admin_dashboard."""
        from engine.features import openAdminDashboard

        with patch("app.admin.open_admin_dashboard", return_value={"status": "success", "url": "http://127.0.0.1:5005/admin"}) as mock_launcher:
            res = openAdminDashboard()
            self.assertEqual(res["status"], "success")
            mock_launcher.assert_called_once()


if __name__ == "__main__":
    unittest.main()
