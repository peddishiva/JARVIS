import pyttsx3


def speak(text, display_fn=None, receiver_fn=None, rate=174, voice_index=0):
    """Convert text to speech using SAPI5 with optional UI hooks."""
    text = str(text)
    try:
        engine = pyttsx3.init("sapi5")
        voices = engine.getProperty("voices")
        if voices and len(voices) > voice_index:
            engine.setProperty("voice", voices[voice_index].id)
        engine.setProperty("rate", rate)

        if display_fn:
            display_fn(text)

        engine.say(text)

        if receiver_fn:
            receiver_fn(text)

        engine.runAndWait()
    except Exception as e:
        print(f"TTS error: {e}")
