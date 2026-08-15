import os
import subprocess
import sqlite3
import struct
import time
import webbrowser
from urllib.parse import quote

import eel
import openai
import pyautogui
import pygame
import pywhatkit as kit
import pyaudio
import pvporcupine
from dotenv import load_dotenv
from openai import OpenAI

from engine.command import speak
from engine.config import ASSISTANT_NAME
from engine.helper import extract_yt_term, remove_words


load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

openrouter_client = None
if OPENROUTER_API_KEY:
    openrouter_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        default_headers={
            "HTTP-Referer": "https://github.com/peddishiva/JARVIS",
            "X-Title": "JARVIS",
        },
    )


conn = sqlite3.connect("jarvis.db")
cursor = conn.cursor()


@eel.expose
def playAssistantSound():
    pygame.mixer.init()
    pygame.mixer.music.load("www\\assets\\audio\\start_sound.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "")
    query.lower()

    app_name = query.strip()

    if app_name != "":
        try:
            cursor.execute(
                "SELECT path FROM sys_command WHERE name IN (?)", (app_name,)
            )
            results = cursor.fetchall()

            if len(results) != 0:
                speak("Opening " + query)
                os.startfile(results[0][0])

            elif len(results) == 0:
                cursor.execute(
                    "SELECT url FROM web_command WHERE name IN (?)", (app_name,)
                )
                results = cursor.fetchall()

                if len(results) != 0:
                    speak("Opening " + query)
                    webbrowser.open(results[0][0])

                else:
                    speak("Opening " + query)
                    try:
                        os.system("start " + query)
                    except Exception:
                        speak("not found")
        except Exception:
            speak("something went wrong")


def PlayYoutube(query):
    search_term = extract_yt_term(query)
    speak("Playing " + search_term + " on YouTube")
    kit.playonyt(search_term)


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
    words_to_remove = [
        ASSISTANT_NAME,
        "make",
        "a",
        "to",
        "phone",
        "call",
        "send",
        "message",
        "wahtsapp",
        "video",
    ]
    query = remove_words(query, words_to_remove)

    try:
        query = query.strip().lower()
        cursor.execute(
            "SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?",
            ("%" + query + "%", query + "%"),
        )
        results = cursor.fetchall()
        print(results[0][0])
        mobile_number_str = str(results[0][0])
        if not mobile_number_str.startswith("+91"):
            mobile_number_str = "+91" + mobile_number_str

        return mobile_number_str, query
    except Exception:
        speak("not exist in contacts")
        return 0, 0


def whatsApp(mobile_no, message, flag, name):
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
    speak(jarvis_message)


def chatBot(query):
    """Send a conversational query to the configured OpenRouter model."""
    if not OPENROUTER_API_KEY or openrouter_client is None:
        message = "OpenRouter is not configured. Add your API key to the .env file."
        print(message)
        speak(message)
        return message

    try:
        response = openrouter_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are JARVIS, a helpful Windows desktop voice assistant. "
                        "Keep answers concise, natural, and suitable for being spoken aloud."
                    ),
                },
                {"role": "user", "content": str(query).strip()},
            ],
        )

        answer = response.choices[0].message.content
        if not answer:
            answer = "I could not generate a response."

        print(answer)
        speak(answer)
        return answer

    except openai.APIConnectionError:
        message = "I cannot reach the OpenRouter service right now."
        print(message)
        speak(message)
        return message
    except openai.AuthenticationError:
        message = "The OpenRouter API key is invalid or expired."
        print(message)
        speak(message)
        return message
    except openai.RateLimitError:
        message = "The OpenRouter request limit has been reached."
        print(message)
        speak(message)
        return message
    except openai.APIError as error:
        message = f"OpenRouter returned an API error: {error}"
        print(message)
        speak(message)
        return message
    except Exception as error:
        message = "Something went wrong while contacting the AI service."
        print(f"{message} {error}")
        speak(message)
        return message
