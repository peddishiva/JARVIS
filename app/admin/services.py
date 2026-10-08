import os
from app.database import get_connection as _raw_get_connection, DEFAULT_DB_PATH
from app.admin.validators import (
    validate_contact,
    validate_web_command,
    validate_system_command,
    DANGEROUS_SHELL_PATTERN,
)


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


def get_connection(db_path=None):
    return _raw_get_connection(_resolve_db_path(db_path))


class ContactsRepository:
    """Repository managing contacts in SQLite."""

    @staticmethod
    def list_all(db_path=None):
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, mobile_no, email FROM contacts ORDER BY name COLLATE NOCASE ASC")
            rows = cursor.fetchall()
            return [{"id": r[0], "name": r[1], "mobile_no": r[2], "email": r[3] or ""} for r in rows]
        finally:
            conn.close()

    @staticmethod
    def search(query, db_path=None):
        query = str(query or "").strip().lower()
        if not query:
            return ContactsRepository.list_all(db_path)

        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, name, mobile_no, email FROM contacts
                   WHERE LOWER(name) LIKE ? OR mobile_no LIKE ? OR LOWER(email) LIKE ?
                   ORDER BY name COLLATE NOCASE ASC""",
                (f"%{query}%", f"%{query}%", f"%{query}%"),
            )
            rows = cursor.fetchall()
            return [{"id": r[0], "name": r[1], "mobile_no": r[2], "email": r[3] or ""} for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_by_id(contact_id, db_path=None):
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, mobile_no, email FROM contacts WHERE id = ?", (contact_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "mobile_no": row[2], "email": row[3] or ""}
            return None
        finally:
            conn.close()

    @staticmethod
    def create(name, mobile_no, email=None, db_path=None):
        valid, err = validate_contact(name, mobile_no, email)
        if not valid:
            return False, err

        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO contacts (name, mobile_no, email) VALUES (?, ?, ?)",
                (name.strip(), mobile_no.strip(), (email or "").strip() or None),
            )
            conn.commit()
            return True, None
        except Exception as e:
            return False, f"Failed to add contact: {e}"
        finally:
            conn.close()

    @staticmethod
    def update(contact_id, name, mobile_no, email=None, db_path=None):
        valid, err = validate_contact(name, mobile_no, email)
        if not valid:
            return False, err

        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE contacts SET name = ?, mobile_no = ?, email = ? WHERE id = ?",
                (name.strip(), mobile_no.strip(), (email or "").strip() or None, contact_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return False, "Contact not found."
            return True, None
        except Exception as e:
            return False, f"Failed to update contact: {e}"
        finally:
            conn.close()

    @staticmethod
    def delete(contact_id, db_path=None):
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return False, "Contact not found."
            return True, None
        except Exception as e:
            return False, f"Failed to delete contact: {e}"
        finally:
            conn.close()


class WebCommandsRepository:
    """Repository managing web shortcut commands in SQLite."""

    @staticmethod
    def list_all(db_path=None):
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, url FROM web_command ORDER BY name COLLATE NOCASE ASC")
            rows = cursor.fetchall()
            return [{"id": r[0], "name": r[1], "url": r[2]} for r in rows]
        finally:
            conn.close()

    @staticmethod
    def search(query, db_path=None):
        query = str(query or "").strip().lower()
        if not query:
            return WebCommandsRepository.list_all(db_path)

        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, url FROM web_command WHERE LOWER(name) LIKE ? OR LOWER(url) LIKE ? ORDER BY name COLLATE NOCASE ASC",
                (f"%{query}%", f"%{query}%"),
            )
            rows = cursor.fetchall()
            return [{"id": r[0], "name": r[1], "url": r[2]} for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_by_id(cmd_id, db_path=None):
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, url FROM web_command WHERE id = ?", (cmd_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "url": row[2]}
            return None
        finally:
            conn.close()

    @staticmethod
    def create(name, url, db_path=None):
        valid, err = validate_web_command(name, url)
        if not valid:
            return False, err

        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            # Case-insensitive duplicate check
            cursor.execute("SELECT 1 FROM web_command WHERE LOWER(name) = ?", (name.strip().lower(),))
            if cursor.fetchone() is not None:
                return False, f"A web command named '{name.strip()}' already exists."

            cursor.execute(
                "INSERT INTO web_command (name, url) VALUES (?, ?)",
                (name.strip().lower(), url.strip()),
            )
            conn.commit()
            return True, None
        except Exception as e:
            return False, f"Failed to add web command: {e}"
        finally:
            conn.close()

    @staticmethod
    def update(cmd_id, name, url, db_path=None):
        valid, err = validate_web_command(name, url)
        if not valid:
            return False, err

        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM web_command WHERE LOWER(name) = ? AND id != ?",
                (name.strip().lower(), cmd_id),
            )
            if cursor.fetchone() is not None:
                return False, f"Another web command named '{name.strip()}' already exists."

            cursor.execute(
                "UPDATE web_command SET name = ?, url = ? WHERE id = ?",
                (name.strip().lower(), url.strip(), cmd_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return False, "Web command not found."
            return True, None
        except Exception as e:
            return False, f"Failed to update web command: {e}"
        finally:
            conn.close()

    @staticmethod
    def delete(cmd_id, db_path=None):
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM web_command WHERE id = ?", (cmd_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return False, "Web command not found."
            return True, None
        except Exception as e:
            return False, f"Failed to delete web command: {e}"
        finally:
            conn.close()


class SystemCommandsRepository:
    """Repository managing system application commands in SQLite."""

    @staticmethod
    def list_all(db_path=None):
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, path FROM sys_command ORDER BY name COLLATE NOCASE ASC")
            rows = cursor.fetchall()
            return [{"id": r[0], "name": r[1], "path": r[2]} for r in rows]
        finally:
            conn.close()

    @staticmethod
    def search(query, db_path=None):
        query = str(query or "").strip().lower()
        if not query:
            return SystemCommandsRepository.list_all(db_path)

        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, path FROM sys_command WHERE LOWER(name) LIKE ? OR LOWER(path) LIKE ? ORDER BY name COLLATE NOCASE ASC",
                (f"%{query}%", f"%{query}%"),
            )
            rows = cursor.fetchall()
            return [{"id": r[0], "name": r[1], "path": r[2]} for r in rows]
        finally:
            conn.close()

    @staticmethod
    def get_by_id(cmd_id, db_path=None):
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, path FROM sys_command WHERE id = ?", (cmd_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "path": row[2]}
            return None
        finally:
            conn.close()

    @staticmethod
    def create(name, path, db_path=None):
        valid, err = validate_system_command(name, path)
        if not valid:
            return False, err

        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM sys_command WHERE LOWER(name) = ?", (name.strip().lower(),))
            if cursor.fetchone() is not None:
                return False, f"A system command named '{name.strip()}' already exists."

            cursor.execute(
                "INSERT INTO sys_command (name, path) VALUES (?, ?)",
                (name.strip().lower(), path.strip()),
            )
            conn.commit()
            return True, None
        except Exception as e:
            return False, f"Failed to add system command: {e}"
        finally:
            conn.close()

    @staticmethod
    def update(cmd_id, name, path, db_path=None):
        valid, err = validate_system_command(name, path)
        if not valid:
            return False, err

        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM sys_command WHERE LOWER(name) = ? AND id != ?",
                (name.strip().lower(), cmd_id),
            )
            if cursor.fetchone() is not None:
                return False, f"Another system command named '{name.strip()}' already exists."

            cursor.execute(
                "UPDATE sys_command SET name = ?, path = ? WHERE id = ?",
                (name.strip().lower(), path.strip(), cmd_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                return False, "System command not found."
            return True, None
        except Exception as e:
            return False, f"Failed to update system command: {e}"
        finally:
            conn.close()

    @staticmethod
    def delete(cmd_id, db_path=None):
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sys_command WHERE id = ?", (cmd_id,))
            conn.commit()
            if cursor.rowcount == 0:
                return False, "System command not found."
            return True, None
        except Exception as e:
            return False, f"Failed to delete system command: {e}"
        finally:
            conn.close()

    @staticmethod
    def test_launch(cmd_id, db_path=None):
        """Safely launch an approved stored command from the database without shell execution."""
        cmd = SystemCommandsRepository.get_by_id(cmd_id, db_path)
        if not cmd:
            return False, "System command not found."

        path = cmd["path"].strip()
        if DANGEROUS_SHELL_PATTERN.search(path):
            return False, "Stored path contains dangerous shell metacharacters and cannot be executed."

        try:
            if hasattr(os, "startfile"):
                os.startfile(path)
                return True, f"Successfully requested Windows to launch '{cmd['name']}'."
            else:
                return False, "Testing executable launching is only supported in Windows environments."
        except Exception as e:
            return False, f"Failed to launch command: {e}"


class DashboardService:
    """Service providing aggregate metrics for the dashboard home screen."""

    @staticmethod
    def get_summary(db_path=None):
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM contacts")
            contacts_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM web_command")
            web_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM sys_command")
            sys_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM admin_user WHERE is_active = 1")
            admin_count = cursor.fetchone()[0]

            openrouter_configured = bool(os.getenv("OPENROUTER_API_KEY"))

            return {
                "contacts_count": contacts_count,
                "web_commands_count": web_count,
                "sys_commands_count": sys_count,
                "admin_users_count": admin_count,
                "openrouter_configured": openrouter_configured,
                "database_status": "Online (SQLite)",
                "database_name": os.path.basename(db_path or DEFAULT_DB_PATH),
            }
        except Exception as e:
            return {
                "contacts_count": 0,
                "web_commands_count": 0,
                "sys_commands_count": 0,
                "admin_users_count": 0,
                "openrouter_configured": False,
                "database_status": f"Error: {e}",
                "database_name": "Unavailable",
            }
        finally:
            conn.close()
