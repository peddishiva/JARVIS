import os
import sys

# Ensure project root is available when executed directly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import (
    DEFAULT_DB_PATH,
    DEFAULT_WEB_COMMANDS,
    init_db,
)

__all__ = [
    "DEFAULT_DB_PATH",
    "DEFAULT_WEB_COMMANDS",
    "init_db",
]

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")