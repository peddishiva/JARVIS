import os
from dotenv import load_dotenv
import openai
from openai import OpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")


def get_openrouter_client():
    """Create and return an OpenRouter OpenAI client if configured."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://github.com/peddishiva/JARVIS",
            "X-Title": "JARVIS",
        },
    )


def chat_bot(query, speak_fn=None, client=None, model=None):
    """Send a conversational query to the configured OpenRouter model."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if client is None:
        client = get_openrouter_client()
    if model is None:
        model = os.getenv("OPENROUTER_MODEL", "openrouter/free")

    if not api_key or client is None:
        message = "OpenRouter is not configured. Add your API key to the .env file."
        print(message)
        if speak_fn:
            speak_fn(message)
        return message

    try:
        response = client.chat.completions.create(
            model=model,
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
        if speak_fn:
            speak_fn(answer)
        return answer

    except openai.APIConnectionError:
        message = "I cannot reach the OpenRouter service right now."
        print(message)
        if speak_fn:
            speak_fn(message)
        return message
    except openai.AuthenticationError:
        message = "The OpenRouter API key is invalid or expired."
        print(message)
        if speak_fn:
            speak_fn(message)
        return message
    except openai.RateLimitError:
        message = "The OpenRouter request limit has been reached."
        print(message)
        if speak_fn:
            speak_fn(message)
        return message
    except openai.APIError as error:
        message = f"OpenRouter returned an API error: {error}"
        print(message)
        if speak_fn:
            speak_fn(message)
        return message
    except Exception as error:
        message = "Something went wrong while contacting the AI service."
        print(f"{message} {error}")
        if speak_fn:
            speak_fn(message)
        return message
