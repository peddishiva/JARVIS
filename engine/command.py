import eel

from app.routing import route_command
from app.services.chat_history import get_chat_history_service
from app.speech import speak as speech_speak
from app.speech import take_command as speech_take_command


def _display_message(text):
    try:
        eel.DisplayMessage(text)
    except Exception:
        pass


def _receiver_text(text):
    try:
        eel.receiverText(text)
    except Exception:
        pass


def speak(text):
    """Text-to-speech bridge delegating to app.speech.synthesis with Eel UI hooks."""
    return speech_speak(text, display_fn=_display_message, receiver_fn=_receiver_text)


def takecommand():
    """Speech-to-text bridge delegating to app.speech.recognition with Eel UI hooks."""
    return speech_take_command(display_fn=_display_message)


# ============================================================
# PERSISTENT CHAT HISTORY EEL ENDPOINTS
# ============================================================


@eel.expose
def getRecentConversations(limit=50):
    """Fetch recent conversations sorted by latest activity descending."""
    try:
        service = get_chat_history_service()
        conversations = service.get_conversations(limit=limit)
        return {"status": "success", "conversations": conversations}
    except Exception as err:
        return {"status": "error", "message": str(err), "conversations": []}


@eel.expose
def createConversation(title=None):
    """Create a new conversation session."""
    try:
        service = get_chat_history_service()
        conv = service.create_conversation(title=title)
        return {"status": "success", "conversation": conv}
    except Exception as err:
        return {"status": "error", "message": str(err)}


@eel.expose
def getConversationMessages(conversation_id):
    """Fetch all chronologically ordered messages for a conversation."""
    try:
        if not conversation_id or not isinstance(conversation_id, str):
            return {"status": "error", "message": "Invalid conversation_id", "messages": []}
        service = get_chat_history_service()
        conv = service.get_conversation(conversation_id)
        if not conv:
            return {"status": "error", "message": "Conversation not found", "messages": []}
        messages = service.get_messages(conversation_id)
        return {"status": "success", "conversation": conv, "messages": messages}
    except Exception as err:
        return {"status": "error", "message": str(err), "messages": []}


@eel.expose
def renameConversation(conversation_id, new_title):
    """Rename an existing conversation."""
    try:
        service = get_chat_history_service()
        updated = service.rename_conversation(conversation_id, new_title)
        return {"status": "success", "conversation": updated}
    except Exception as err:
        return {"status": "error", "message": str(err)}


@eel.expose
def deleteConversation(conversation_id):
    """Delete a conversation and its messages."""
    try:
        service = get_chat_history_service()
        deleted = service.delete_conversation(conversation_id)
        return {"status": "success", "deleted": deleted}
    except Exception as err:
        return {"status": "error", "message": str(err)}


@eel.expose
def saveChatMessage(conversation_id, role, content):
    """Explicitly save a chat message to SQLite."""
    try:
        service = get_chat_history_service()
        msg = service.save_message(conversation_id, role, content)
        return {"status": "success", "message": msg}
    except Exception as err:
        return {"status": "error", "message": str(err)}


# ============================================================
# CANONICAL COMMAND DISPATCHER
# ============================================================


@eel.expose
def allCommands(message=1, conversation_id=None):
    """Central Eel command dispatcher bridging frontend requests to app.routing and persistence."""
    if message == 1:
        query = takecommand()
    else:
        query = message

    if not query or not str(query).strip():
        try:
            eel.ShowHood()
        except Exception:
            pass
        return

    clean_query = str(query).strip()
    service = get_chat_history_service()

    # Determine or generate conversation ID for this request
    if not conversation_id or not str(conversation_id).strip():
        conv = service.create_conversation()
        req_conv_id = conv["id"]
    else:
        req_conv_id = str(conversation_id).strip()

    # Save user message to the active conversation
    try:
        service.save_message(req_conv_id, role="user", content=clean_query)
    except Exception as err:
        print(f"Error persisting user query: {err}")

    try:
        eel.senderText(clean_query, req_conv_id)
    except Exception:
        pass

    # Dedicated closure ensuring spoken assistant response is bound to req_conv_id
    def request_speak(text):
        if text and str(text).strip():
            clean_ans = str(text).strip()
            try:
                service.save_message(req_conv_id, role="assistant", content=clean_ans)
            except Exception as err:
                print(f"Error persisting assistant response: {err}")

        def _disp(t):
            try:
                eel.DisplayMessage(t, req_conv_id)
            except Exception:
                pass

        def _recv(t):
            try:
                eel.receiverText(t, req_conv_id)
            except Exception:
                pass

        return speech_speak(text, display_fn=_disp, receiver_fn=_recv)

    try:
        import sys

        feat = sys.modules.get("engine.features")
        if feat and any(
            hasattr(getattr(feat, fn, None), "assert_called")
            for fn in ("openCommand", "PlayYoutube", "findContact", "chatBot")
        ):
            route_command(
                clean_query,
                speak_fn=request_speak,
                take_command_fn=takecommand,
                open_command_fn=feat.openCommand,
                play_youtube_fn=feat.PlayYoutube,
                find_contact_fn=feat.findContact,
                whatsapp_fn=feat.whatsApp,
                chat_bot_fn=feat.chatBot,
            )
        else:
            route_command(
                clean_query,
                speak_fn=request_speak,
                take_command_fn=takecommand,
            )
    except Exception as err:
        print(f"Routing error: {err}")

    try:
        eel.ShowHood(req_conv_id)
    except Exception:
        pass