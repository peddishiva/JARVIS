# JARVIS

A Windows-first Python desktop voice assistant with a local Eel web UI. JARVIS combines speech recognition, text-to-speech, hotword detection, desktop/web app launching, YouTube playback, WhatsApp automation, SQLite-backed commands and contacts, and an LLM accessed through OpenRouter.

## Features

- Voice input using `SpeechRecognition` and the system microphone.
- Voice output using `pyttsx3` with Windows SAPI5.
- Wake-word detection for **JARVIS** / **Alexa** using Picovoice Porcupine.
- Desktop UI built with **Eel** and the files under `www/`.
- Opens Windows applications and registered web commands from SQLite.
- Plays YouTube searches through `pywhatkit`.
- Sends WhatsApp messages and starts WhatsApp calls/video calls through Windows URL and keyboard automation.
- Conversational AI through the **OpenRouter API**.
- Configurable OpenRouter model through an environment variable.

## Requirements

JARVIS is currently designed for **Windows**. The application starts Microsoft Edge in app mode and uses Windows-specific functionality such as SAPI5 and `os.startfile`.

You need:

- Windows 10 or Windows 11
- Python 3.10+ (Python 3.12 is a reasonable choice for this repository)
- A working microphone
- Speakers or headphones
- Microsoft Edge
- WhatsApp Desktop or a Windows environment that can open `whatsapp://` links
- An OpenRouter API key for AI chat

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/peddishiva/JARVIS.git
cd JARVIS
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure OpenRouter

Create your local environment file:

```powershell
copy .env.example .env
```

Open `.env` and set:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openrouter/free
```

JARVIS uses OpenRouter's OpenAI-compatible API endpoint. The API key stays in `.env` and is excluded from Git by `.gitignore`.

`openrouter/free` is used as the default model router. You can replace it with another OpenRouter model ID whenever you want without changing the Python code.

### 5. Prepare the local database

JARVIS expects a local SQLite database named `jarvis.db` in the project root. It is intentionally ignored by Git because it can contain personal contacts and machine-specific application paths.

The database helper in `engine/db.py` contains example SQL for these tables:

- `sys_command` — application names and Windows executable paths.
- `web_command` — command names and web URLs.
- `contacts` — contact names and mobile numbers used by WhatsApp automation.

If you already have a working `jarvis.db`, place it in the project root. Otherwise initialize the required tables using the examples in `engine/db.py` before using database-backed commands.

### 6. Start JARVIS

For the normal launcher, which starts the UI and hotword listener in separate processes:

```powershell
python run.py
```

To start only the Eel UI process:

```powershell
python main.py
```

The UI launcher initializes `www/`, plays the startup sound, and opens Microsoft Edge at the local JARVIS page.

## How It Works

```text
Microphone
    │
    ▼
Porcupine Hotword Listener
    │
    └── "Jarvis" / "Alexa"
             │
             ▼
          Win + J
             │
             ▼
       Eel Web Interface
             │
             ▼
      Speech Recognition
             │
             ▼
       Command Router
       ┌─────┼──────────────┬─────────────┐
       ▼     ▼              ▼             ▼
     System  Web          YouTube      WhatsApp
     Apps    Commands      Search       Actions
       │     │              │             │
       └─────┴──────────────┴─────────────┘
                         │
                         ▼
                 OpenRouter API
                         │
                         ▼
                  Configured LLM
                         │
                         ▼
                    pyttsx3/SAPI5
```

Normal conversational requests are routed to `chatBot()`, which sends the request to the configured OpenRouter model and then speaks the returned response.

## Project Structure

```text
JARVIS/
├── engine/
│   ├── command.py       # Speech recognition and command routing
│   ├── config.py        # Assistant name
│   ├── db.py            # SQLite schema/data helper code
│   ├── features.py      # Assistant features and OpenRouter LLM integration
│   └── helper.py        # Text/YouTube helpers
├── www/
│   ├── assets/          # Audio, icon and vendor assets
│   ├── controller.js
│   ├── index.html       # Eel UI entry page
│   ├── main.js
│   ├── script.js
│   └── style.css
├── .env.example         # OpenRouter configuration template
├── .gitignore
├── main.py              # Starts the Eel application
├── run.py               # Starts UI + hotword listener
├── requirements.txt     # Python dependencies
└── README.md
```

## OpenRouter Configuration

The LLM integration is intentionally isolated to `chatBot()` in `engine/features.py`.

Environment variables:

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENROUTER_API_KEY` | Yes for AI chat | — | Your OpenRouter API key |
| `OPENROUTER_MODEL` | No | `openrouter/free` | OpenRouter model/router ID |

Do **not** put the API key directly in Python source code or commit `.env` to GitHub.

## Example Commands

```text
Open YouTube
Open Notepad
Play Believer on YouTube
Send a message to Shiva
Phone call to Shiva
Video call to Shiva
What is machine learning?
Explain recursion in simple words
```

The exact application names available through `open ...` depend on the entries in your local `jarvis.db`.

## Troubleshooting

### `ModuleNotFoundError`

Activate the virtual environment and reinstall dependencies:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### PyAudio installation fails

Make sure you are using a supported Windows/Python combination and upgrade pip:

```powershell
python -m pip install --upgrade pip
pip install PyAudio
```

### Microphone does not work

Check Windows microphone permissions, confirm the correct input device is selected, and test the microphone in another application.

### JARVIS starts but Edge does not open

`main.py` invokes `msedge.exe` directly. Make sure Microsoft Edge is installed and available through the Windows command path.

### Hotword detection does not start

The hotword listener uses Porcupine and PyAudio with the default microphone. Check microphone permissions and confirm both packages installed successfully.

### OpenRouter says the API key is missing

Make sure `.env` exists in the project root and contains:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

Restart JARVIS after changing `.env`.

### OpenRouter authentication fails

Verify that the key is valid, has not been revoked, and is copied without surrounding quotes or extra spaces.

### The selected model is unavailable

Change `OPENROUTER_MODEL` to a currently available model ID in OpenRouter. The default `openrouter/free` router may also change which underlying free model serves a request.

### WhatsApp automation fails

The current implementation relies on Windows `whatsapp://send?...` links and `pyautogui` keyboard automation. Make sure WhatsApp is installed/configured and that the target contact exists in `jarvis.db`.

## Security Notes

- Keep `OPENROUTER_API_KEY` in `.env` and never commit it.
- Do not commit personal contacts or machine-specific paths from `jarvis.db`.
- Do not commit authentication cookies or session data.
- JARVIS can launch applications and automate external services, so only run commands you trust.

## Development Commands

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
python main.py
deactivate
```

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Test changes on Windows.
4. Keep API keys, cookies, contacts, and other personal data out of commits.
5. Open a pull request with a clear description of the change.

## License

No license file is currently present in the repository. Unless a license is added, the source should not be assumed to be available for unrestricted reuse, redistribution, or modification.

## Acknowledgements

JARVIS uses Python and web technologies including Eel, OpenRouter, OpenAI's Python client, PyAudio, SpeechRecognition, pyttsx3, pygame, PyAutoGUI, PyWhatKit, Picovoice Porcupine, SQLite, HTML, CSS, and JavaScript.
