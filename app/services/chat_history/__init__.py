"""JARVIS Chat History and Conversations Service."""

from app.services.chat_history.service import (
    ChatHistoryService,
    generate_conversation_title,
)

_service_instance = None


def get_chat_history_service(db_path=None):
    """Factory returning ChatHistoryService instance."""
    global _service_instance
    if db_path is not None:
        return ChatHistoryService(db_path=db_path)
    if _service_instance is None:
        _service_instance = ChatHistoryService()
    return _service_instance


__all__ = [
    "ChatHistoryService",
    "generate_conversation_title",
    "get_chat_history_service",
]
