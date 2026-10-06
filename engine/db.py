import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "jarvis.db")

DEFAULT_WEB_COMMANDS = [
    ("youtube", "https://www.youtube.com/"),
    ("google", "https://www.google.com/"),
    ("canva", "https://www.canva.com/"),
    ("amazon", "https://www.amazon.in/"),
    ("flipkart", "https://www.flipkart.com/"),
    ("myntra", "https://www.myntra.com/"),
    ("instagram", "https://www.instagram.com/"),
    ("snapchat", "https://www.snapchat.com/"),
    ("ajio", "https://www.ajio.com/"),
    ("blackbox", "https://www.blackbox.ai/"),
    ("chatgpt", "https://chatgpt.com/"),
]


def init_db(db_path=None):
    """Initialize the JARVIS database schema and safe default web commands.

    Idempotent and safe: preserves existing tables, custom URLs, and user records.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Exact production schema reproduction
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sys_command(
            id integer primary key,
            name VARCHAR(100),
            path VARCHAR(1000)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS web_command(
            id integer primary key,
            name VARCHAR(100),
            url VARCHAR(1000)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS contacts(
            id integer primary key,
            name VARCHAR(200),
            mobile_no VARCHAR(255),
            email VARCHAR(255) NULL
        )
        """
    )

    # Seed safe web commands idempotently without relying on UNIQUE constraint
    for name, url in DEFAULT_WEB_COMMANDS:
        cursor.execute("SELECT 1 FROM web_command WHERE LOWER(name) = ?", (name.lower(),))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO web_command (name, url) VALUES (?, ?)", (name, url))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")