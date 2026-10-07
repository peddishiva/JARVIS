import time
import speech_recognition as sr


def take_command(display_fn=None, language="en-in", pause_threshold=1, timeout=10, phrase_time_limit=6):
    """Listen for audio from microphone and recognize speech to text."""
    r = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("listening...")
            if display_fn:
                display_fn("listening...")
            r.pause_threshold = pause_threshold
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, timeout, phrase_time_limit)
    except Exception as e:
        print(f"Microphone error: {e}")
        return ""

    try:
        print("Recognizing...")
        if display_fn:
            display_fn("Recognizing...")
        query = r.recognize_google(audio, language=language)
        print(f"user said: {query}")
        if display_fn:
            display_fn(query)
        time.sleep(3)
        return query.lower()
    except Exception:
        return ""
