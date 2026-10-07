import re
import pywhatkit as kit


def extract_yt_term(command):
    """Extract search/song term from YouTube voice or text command."""
    if not command or not isinstance(command, str):
        return None
    pattern = r"play\s+(.*?)\s+on\s+youtube"
    match = re.search(pattern, command, re.IGNORECASE)
    if match and match.group(1).strip():
        return match.group(1).strip()
    return None


def play_youtube(query, speak_fn=None, player_fn=None):
    """Extract YouTube term and launch playback via pywhatkit."""
    if player_fn is None:
        player_fn = kit.playonyt

    search_term = extract_yt_term(query)
    if not search_term:
        if speak_fn:
            speak_fn("What would you like to play on YouTube?")
        return

    if speak_fn:
        speak_fn("Playing " + search_term + " on YouTube")
    player_fn(search_term)
