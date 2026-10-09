import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "jarvis.db")


def get_connection(db_path=None):
    """Return a sqlite3 connection for the specified or default database path.

    Creates parent directories if required by custom paths.
    Does not maintain global connection or cursor state.
    """
    if db_path is None:
        db_path = os.environ.get("JARVIS_DB_PATH") or DEFAULT_DB_PATH

    dir_name = os.path.dirname(os.path.abspath(db_path))
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
