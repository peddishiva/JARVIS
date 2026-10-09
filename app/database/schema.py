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

CONVERSATIONS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS conversations(
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_archived INTEGER DEFAULT 0
)
"""

MESSAGES_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS messages(
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sequence_number INTEGER NOT NULL,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
)
"""

CONVERSATIONS_INDEX_DDL = """
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC)
"""

MESSAGES_INDEX_DDL = """
CREATE INDEX IF NOT EXISTS idx_messages_conversation_seq ON messages(conversation_id, sequence_number ASC)
"""


def initialize_schema(connection):
    """Execute the authoritative schema DDL against the provided connection."""
    cursor = connection.cursor()
    cursor.execute(SYS_COMMAND_TABLE_DDL)
    cursor.execute(WEB_COMMAND_TABLE_DDL)
    cursor.execute(CONTACTS_TABLE_DDL)
    cursor.execute(ADMIN_USER_TABLE_DDL)
    cursor.execute(CONVERSATIONS_TABLE_DDL)
    cursor.execute(MESSAGES_TABLE_DDL)
    cursor.execute(CONVERSATIONS_INDEX_DDL)
    cursor.execute(MESSAGES_INDEX_DDL)
