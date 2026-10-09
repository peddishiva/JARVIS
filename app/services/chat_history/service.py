import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from app.database.connection import get_connection


def generate_conversation_title(first_query: str, max_length: int = 50) -> str:
    """Generate a clean, local conversation title from the first user query."""
    if not first_query or not isinstance(first_query, str):
        return "New Conversation"

    # Normalize whitespace and newlines
    cleaned = " ".join(first_query.strip().split())
    if not cleaned:
        return "New Conversation"

    # Capitalize first character cleanly
    title = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
    if len(title) > max_length:
        return title[: max_length - 3].rstrip() + "..."
    return title


class ChatHistoryService:
    """Domain service for managing persistent conversations and messages in SQLite."""

    def __init__(self, db_path=None):
        self.db_path = db_path

    @contextmanager
    def _get_conn(self):
        conn = get_connection(self.db_path)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def create_conversation(self, title=None, conversation_id=None) -> dict:
        """Create a new conversation record."""
        conv_id = conversation_id or f"conv_{uuid.uuid4().hex[:16]}"
        safe_title = (title or "New Conversation").strip()
        if not safe_title:
            safe_title = "New Conversation"

        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversations (id, title, created_at, updated_at, is_archived)
                VALUES (?, ?, ?, ?, 0)
                """,
                (conv_id, safe_title, now, now),
            )
            conn.commit()

        return {
            "id": conv_id,
            "title": safe_title,
            "created_at": now,
            "updated_at": now,
            "is_archived": 0,
        }

    def get_conversations(self, limit=50, offset=0, include_archived=False) -> list[dict]:
        """List conversations ordered by last activity descending."""
        try:
            limit = max(1, min(int(limit), 200))
        except (ValueError, TypeError):
            limit = 50
        try:
            offset = max(0, int(offset))
        except (ValueError, TypeError):
            offset = 0

        query = "SELECT id, title, created_at, updated_at, is_archived FROM conversations"
        params = []
        if not include_archived:
            query += " WHERE is_archived = 0"
        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [
            {
                "id": r[0],
                "title": r[1],
                "created_at": r[2],
                "updated_at": r[3],
                "is_archived": r[4],
            }
            for r in rows
        ]

    def get_conversation(self, conversation_id: str) -> dict | None:
        """Retrieve single conversation metadata by ID."""
        if not conversation_id or not isinstance(conversation_id, str):
            return None
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, created_at, updated_at, is_archived FROM conversations WHERE id = ?",
                (conversation_id.strip(),),
            )
            row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "title": row[1],
            "created_at": row[2],
            "updated_at": row[3],
            "is_archived": row[4],
        }

    def get_messages(self, conversation_id: str) -> list[dict]:
        """Retrieve all messages for a conversation in deterministic chronological sequence."""
        if not conversation_id or not isinstance(conversation_id, str):
            return []
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, conversation_id, role, content, created_at, sequence_number
                FROM messages
                WHERE conversation_id = ?
                ORDER BY sequence_number ASC
                """,
                (conversation_id.strip(),),
            )
            rows = cursor.fetchall()

        return [
            {
                "id": r[0],
                "conversation_id": r[1],
                "role": r[2],
                "content": r[3],
                "created_at": r[4],
                "sequence_number": r[5],
            }
            for r in rows
        ]

    def save_message(self, conversation_id: str, role: str, content: str) -> dict:
        """Persist a message, update conversation activity timestamp, and auto-title on first query."""
        if not conversation_id or not isinstance(conversation_id, str):
            raise ValueError("Invalid conversation_id")
        conv_id = conversation_id.strip()

        if role not in ("user", "assistant", "system"):
            raise ValueError(f"Invalid role: {role}")

        content_str = str(content or "").strip()
        if not content_str:
            raise ValueError("Message content cannot be empty")

        now = datetime.now(timezone.utc).isoformat()
        msg_id = f"msg_{uuid.uuid4().hex[:16]}"

        with self._get_conn() as conn:
            cursor = conn.cursor()
            # 1. Verify conversation exists, or create it if not found
            cursor.execute("SELECT id, title FROM conversations WHERE id = ?", (conv_id,))
            conv_row = cursor.fetchone()
            if not conv_row:
                title = generate_conversation_title(content_str) if role == "user" else "New Conversation"
                cursor.execute(
                    """
                    INSERT INTO conversations (id, title, created_at, updated_at, is_archived)
                    VALUES (?, ?, ?, ?, 0)
                    """,
                    (conv_id, title, now, now),
                )
            else:
                # If conversation still has default title and this is a user message, update title
                current_title = conv_row[1]
                if current_title == "New Conversation" and role == "user":
                    new_title = generate_conversation_title(content_str)
                    cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", (new_title, conv_id))

            # 2. Sequence ordering
            cursor.execute("SELECT COALESCE(MAX(sequence_number), 0) FROM messages WHERE conversation_id = ?", (conv_id,))
            seq_num = cursor.fetchone()[0] + 1

            # 3. Deduplication check (prevent identical duplicate consecutive saves within same second)
            cursor.execute(
                """
                SELECT id FROM messages
                WHERE conversation_id = ? AND role = ? AND content = ? AND sequence_number = ?
                """,
                (conv_id, role, content_str, seq_num - 1),
            )
            dup = cursor.fetchone()
            if dup:
                cursor.execute("SELECT id, conversation_id, role, content, created_at, sequence_number FROM messages WHERE id = ?", (dup[0],))
                existing = cursor.fetchone()
                return {
                    "id": existing[0],
                    "conversation_id": existing[1],
                    "role": existing[2],
                    "content": existing[3],
                    "created_at": existing[4],
                    "sequence_number": existing[5],
                }

            # 4. Insert message
            cursor.execute(
                """
                INSERT INTO messages (id, conversation_id, role, content, created_at, sequence_number)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (msg_id, conv_id, role, content_str, now, seq_num),
            )

            # 5. Bump conversation updated_at
            cursor.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))
            conn.commit()

        return {
            "id": msg_id,
            "conversation_id": conv_id,
            "role": role,
            "content": content_str,
            "created_at": now,
            "sequence_number": seq_num,
        }

    def rename_conversation(self, conversation_id: str, new_title: str) -> dict:
        """Rename an existing conversation."""
        if not conversation_id or not isinstance(conversation_id, str):
            raise ValueError("Invalid conversation_id")
        conv_id = conversation_id.strip()

        title_str = str(new_title or "").strip()
        if not title_str:
            raise ValueError("Conversation title cannot be empty")
        if len(title_str) > 100:
            title_str = title_str[:100].strip()

        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title_str, now, conv_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(f"Conversation {conv_id} not found")
            conn.commit()

        return self.get_conversation(conv_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and its associated messages."""
        if not conversation_id or not isinstance(conversation_id, str):
            raise ValueError("Invalid conversation_id")
        conv_id = conversation_id.strip()

        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Explicit cascaded delete inside atomic transaction
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
            deleted = cursor.rowcount > 0
            conn.commit()

        return deleted
