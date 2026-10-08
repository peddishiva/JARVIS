"""JARVIS application configuration."""

import os
from dotenv import load_dotenv

load_dotenv()

ASSISTANT_NAME = "jarvis"

# Admin Dashboard configuration (Phase 5)
ADMIN_HOST = os.getenv("ADMIN_HOST", "127.0.0.1")
ADMIN_PORT = int(os.getenv("ADMIN_PORT", "5005"))
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY")
