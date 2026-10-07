import re

def extract_yt_term(command):
    if not command or not isinstance(command, str):
        return None
    # Define a regular expression pattern to capture the song name
    pattern = r'play\s+(.*?)\s+on\s+youtube'
    # Use re.search to find the match in the command
    match = re.search(pattern, command, re.IGNORECASE)
    # If a match is found and non-empty, return the extracted song name; otherwise, return None
    if match and match.group(1).strip():
        return match.group(1).strip()
    return None


from app.core.text_utils import remove_words

__all__ = ["extract_yt_term", "remove_words"]
