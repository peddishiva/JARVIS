from app.database.connection import DEFAULT_DB_PATH, get_connection
from app.database.schema import initialize_schema
from app.database.seed import DEFAULT_WEB_COMMANDS, seed_default_web_commands


def init_db(db_path=None):
    """Initialize the JARVIS database schema and safe default web commands.

    Orchestrates connection, schema creation, default seeding, commit, and cleanly closes.
    Idempotent and safe: preserves existing tables, custom URLs, and user records.
    """
    conn = get_connection(db_path)
    try:
        initialize_schema(conn)
        seed_default_web_commands(conn)
        conn.commit()
    finally:
        conn.close()


__all__ = [
    "DEFAULT_DB_PATH",
    "DEFAULT_WEB_COMMANDS",
    "get_connection",
    "init_db",
]
