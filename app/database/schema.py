SYS_COMMAND_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS sys_command(
    id integer primary key,
    name VARCHAR(100),
    path VARCHAR(1000)
)
"""

WEB_COMMAND_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS web_command(
    id integer primary key,
    name VARCHAR(100),
    url VARCHAR(1000)
)
"""

CONTACTS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS contacts(
    id integer primary key,
    name VARCHAR(200),
    mobile_no VARCHAR(255),
    email VARCHAR(255) NULL
)
"""

ADMIN_USER_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS admin_user(
    id integer primary key,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
)
"""


def initialize_schema(connection):
    """Execute the authoritative schema DDL against the provided connection."""
    cursor = connection.cursor()
    cursor.execute(SYS_COMMAND_TABLE_DDL)
    cursor.execute(WEB_COMMAND_TABLE_DDL)
    cursor.execute(CONTACTS_TABLE_DDL)
    cursor.execute(ADMIN_USER_TABLE_DDL)
