import os
import sqlite3
import struct
import time

import eel
import pyaudio
import pvporcupine
import pygame
import pywhatkit as kit

from app.database import DEFAULT_DB_PATH, init_db
from app.services.llm import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    chat_bot,
    get_openrouter_client,
)
from app.services.system import open_command
from app.services.whatsapp import find_contact, send_whatsapp_message
from app.services.youtube import play_youtube
from engine.command import speak
from engine.config import ASSISTANT_NAME
from engine.helper import extract_yt_term, remove_words

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUND_PATH = os.path.join(BASE_DIR, "www", "assets", "audio", "start_sound.mp3")

openrouter_client = get_openrouter_client()

init_db()
conn = sqlite3.connect(DEFAULT_DB_PATH)
cursor = conn.cursor()


@eel.expose
def playAssistantSound():
    pygame.mixer.init()
    if os.path.exists(SOUND_PATH):
        pygame.mixer.music.load(SOUND_PATH)
    else:
        pygame.mixer.music.load("www\\assets\\audio\\start_sound.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


def openCommand(query):
    return open_command(query, speak_fn=speak)


def PlayYoutube(query):
    return play_youtube(query, speak_fn=speak, player_fn=kit.playonyt)


def hotword():
    porcupine = None
    paud = None
    audio_stream = None
    try:
        porcupine = pvporcupine.create(keywords=["jarvis", "alexa"])
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
        )

        while True:
            keyword = audio_stream.read(porcupine.frame_length)
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)
            keyword_index = porcupine.process(keyword)

            if keyword_index >= 0:
                print("hotword detected")
                import pyautogui as autogui
                autogui.keyDown("win")
                autogui.press("j")
                time.sleep(2)
                autogui.keyUp("win")

    except Exception:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()


def findContact(query):
    return find_contact(query, speak_fn=speak)


def whatsApp(mobile_no, message, flag, name):
    return send_whatsapp_message(mobile_no, message, flag, name, speak_fn=speak)


def chatBot(query):
    """Send a conversational query to the configured OpenRouter model."""
    return chat_bot(
        query,
        speak_fn=speak,
        client=openrouter_client,
        model=OPENROUTER_MODEL,
    )
