from app.services.llm import chat_bot
from app.services.system import open_command
from app.services.whatsapp import find_contact, send_whatsapp_message
from app.services.youtube import play_youtube


def route_command(
    query,
    speak_fn=None,
    take_command_fn=None,
    open_command_fn=None,
    play_youtube_fn=None,
    find_contact_fn=None,
    whatsapp_fn=None,
    chat_bot_fn=None,
):
    """Analyze query intent and dispatch to the appropriate service."""
    if open_command_fn is None:
        open_command_fn = lambda q: open_command(q, speak_fn=speak_fn)
    if play_youtube_fn is None:
        play_youtube_fn = lambda q: play_youtube(q, speak_fn=speak_fn)
    if find_contact_fn is None:
        find_contact_fn = lambda q: find_contact(q, speak_fn=speak_fn)
    if whatsapp_fn is None:
        whatsapp_fn = lambda num, q, msg, name: send_whatsapp_message(
            num, q, msg, name, speak_fn=speak_fn
        )
    if chat_bot_fn is None:
        chat_bot_fn = lambda q: chat_bot(q, speak_fn=speak_fn)

    normalized_query = (
        query.lower().strip()
        if isinstance(query, str)
        else str(query).lower().strip()
    )

    if "open" in normalized_query:
        open_command_fn(normalized_query)
    elif "on youtube" in normalized_query:
        play_youtube_fn(query)
    elif (
        "send a message" in normalized_query
        or "phone call" in normalized_query
        or "video call" in normalized_query
    ):
        contact_no, name = find_contact_fn(normalized_query)
        if contact_no != 0:
            if "send a message" in normalized_query:
                message = "message"
                if speak_fn:
                    speak_fn("what message to send")
                if take_command_fn:
                    query = take_command_fn()
                else:
                    query = ""
            elif "phone call" in normalized_query:
                message = "call"
            else:
                message = "video call"

            whatsapp_fn(contact_no, query, message, name)
    else:
        chat_bot_fn(query)
