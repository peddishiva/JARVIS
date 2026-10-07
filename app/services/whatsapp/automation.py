import subprocess
import time
from urllib.parse import quote

import pyautogui

from app.config import ASSISTANT_NAME
from app.core.text_utils import remove_words
from app.database import get_connection


def find_contact(query, speak_fn=None, db_path=None):
    """Find a contact's phone number matching the query."""
    words_to_remove = [
        ASSISTANT_NAME,
        "make",
        "a",
        "to",
        "phone",
        "call",
        "send",
        "message",
        "whatsapp",
        "video",
    ]
    query = remove_words(query, words_to_remove)

    conn = get_connection(db_path)
    try:
        query = query.strip().lower()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?",
            ("%" + query + "%", query + "%"),
        )
        results = cursor.fetchall()
        mobile_number_str = str(results[0][0])
        if not mobile_number_str.startswith("+91"):
            mobile_number_str = "+91" + mobile_number_str

        return mobile_number_str, query
    except Exception:
        if speak_fn:
            speak_fn("not exist in contacts")
        return 0, 0
    finally:
        conn.close()


def send_whatsapp_message(mobile_no, message, flag, name, speak_fn=None):
    """Automate sending a WhatsApp message or starting a call."""
    if flag == "message":
        target_tab = 19
        jarvis_message = "message sent successfully to " + name
    elif flag == "call":
        target_tab = 14
        message = ""
        jarvis_message = "starting calling to " + name
    else:
        target_tab = 13
        message = ""
        jarvis_message = "starting video call with " + name

    encoded_message = quote(message)
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"
    full_command = f'start "" "{whatsapp_url}"'

    subprocess.run(full_command, shell=True)
    time.sleep(5)
    subprocess.run(full_command, shell=True)

    pyautogui.hotkey("ctrl", "f")
    for _ in range(1, target_tab):
        pyautogui.hotkey("tab")
    pyautogui.hotkey("enter")
    if speak_fn:
        speak_fn(jarvis_message)
