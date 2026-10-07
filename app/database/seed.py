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


def seed_default_web_commands(connection):
    """Seed safe portable default web commands idempotently.

    Uses explicit case-insensitive existence checks to avoid duplicates
    without modifying existing entries or overwriting custom URLs.
    """
    cursor = connection.cursor()
    for name, url in DEFAULT_WEB_COMMANDS:
        cursor.execute("SELECT 1 FROM web_command WHERE LOWER(name) = ?", (name.lower(),))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO web_command (name, url) VALUES (?, ?)", (name, url))
