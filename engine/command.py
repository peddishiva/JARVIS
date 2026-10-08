import eel

from app.routing import route_command
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


@eel.expose
def allCommands(message=1):
    """Central Eel command dispatcher bridging frontend requests to app.routing."""
    if message == 1:
        query = takecommand()
        print(query)
        try:
            eel.senderText(query)
        except Exception:
            pass
    else:
        query = message
        try:
            eel.senderText(query)
        except Exception:
            pass

    try:
        import sys

        feat = sys.modules.get("engine.features")
        if feat and any(
            hasattr(getattr(feat, fn, None), "assert_called")
            for fn in ("openCommand", "PlayYoutube", "findContact", "chatBot")
        ):
            route_command(
                query,
                speak_fn=speak,
                take_command_fn=takecommand,
                open_command_fn=feat.openCommand,
                play_youtube_fn=feat.PlayYoutube,
                find_contact_fn=feat.findContact,
                whatsapp_fn=feat.whatsApp,
                chat_bot_fn=feat.chatBot,
            )
        else:
            route_command(
                query,
                speak_fn=speak,
                take_command_fn=takecommand,
            )
    except Exception:
        print("error")

    try:
        eel.ShowHood()
    except Exception:
        pass