# JARVIS

A Windows-first Python desktop voice assistant with a local Eel web UI. JARVIS combines speech recognition, text-to-speech, hotword detection, desktop/web app launching, YouTube playback, WhatsApp automation, SQLite-backed commands and contacts, and an LLM accessed through OpenRouter.

## Features

- Voice input using `SpeechRecognition` and the system microphone.
- Voice output using `pyttsx3` with Windows SAPI5.
- Wake-word detection for **JARVIS** / **Alexa** using Picovoice Porcupine.
- **ChatGPT-Style Conversation Interface**: Modern conversation stream with user/assistant bubbles, syntax highlighting, and an anchored bottom chat composer with independent message scrolling.
- **Persistent Chat History & Recent Chats**: Database-backed conversation management in SQLite with automated title generation, conversation switching, renaming, and deletion.
- Desktop UI built with **Eel** and frontend assets under `www/`.
- **Admin Dashboard (Phase 5)** built with Flask, providing local administrative control for contacts, web commands, system commands, and authentication.
- Opens Windows applications and registered web commands from SQLite.
- Plays YouTube searches through `pywhatkit`.
- Sends WhatsApp messages and starts WhatsApp calls/video calls through Windows URL and keyboard automation.
- Conversational AI through the **OpenRouter API**.
- Configurable OpenRouter model through an environment variable.

## Requirements

JARVIS is designed for **Windows**. The application starts Microsoft Edge in app mode and uses Windows-specific functionality such as SAPI5 and `os.startfile`.

You need:

- Windows 10 or Windows 11
- Python 3.10+ (Python 3.12 or 3.13)
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

### 4. Configure Environment Variables

Create your local environment file:

```powershell
copy .env.example .env
```

Open `.env` and set:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openrouter/free

# Admin Dashboard configuration (optional overrides)
ADMIN_HOST=127.0.0.1
ADMIN_PORT=5005
```

JARVIS uses OpenRouter's OpenAI-compatible API endpoint. The API key stays in `.env` and is excluded from Git by `.gitignore`.

`openrouter/free` is used as the default model router. You can replace it with another OpenRouter model ID whenever you want without changing the Python code.

### 5. Local Database Setup

JARVIS uses a local SQLite database named `jarvis.db` in the project root. It is intentionally ignored by Git because it contains local user data, personal contacts, administrator credentials, and machine-specific application paths.

Database initialization is managed authoritatively by `app.database`:
- Schema initialization and default seeding run automatically on application startup.
- You can also run initialization manually via PowerShell:

```powershell
python -c "from app.database import init_db; init_db()"
```

The database schema defines the following tables:
- `conversations` — persistent chat conversation threads (`id`, `title`, `created_at`, `updated_at`, `is_archived`).
- `messages` — ordered conversation messages (`id`, `conversation_id`, `role`, `content`, `created_at`, `sequence_number`).
- `admin_user` — administrator account credentials (`username`, `password_hash`, `is_active`).
- `contacts` — contact names and mobile numbers used by WhatsApp automation.
- `web_command` — command names and web URLs (pre-seeded with popular defaults).
- `sys_command` — application shortcuts and Windows executable paths.

Users should populate their own local database with personal contacts and installed application paths.

### 6. Start JARVIS

For the complete application launcher, which orchestrates the Eel UI, background Porcupine hotword listener, and local Admin Dashboard in separate processes:

```powershell
python run.py
```

To start only the Eel UI assistant process:

```powershell
python main.py
```

To start only the Admin Dashboard web server:

```powershell
python -m app.admin
```

The UI launcher initializes `www/`, plays the startup sound, and opens Microsoft Edge at the local JARVIS page. The Admin Dashboard becomes available at `http://127.0.0.1:5005/admin`.

## Admin Dashboard (Phase 5)

JARVIS includes a dedicated, local-first Admin Dashboard served at `http://127.0.0.1:5005/admin`.

### First-Time Administrator Setup

When accessing the dashboard for the first time without any administrator accounts configured:
1. Navigate to `http://127.0.0.1:5005/admin` in any browser.
2. The dashboard automatically redirects to `/admin/setup`.
3. Enter your desired administrator username and a strong password (minimum 8 characters).
4. The password is hashed using NIST-approved **scrypt** key derivation before being committed to SQLite. Plaintext passwords are never stored or logged.
5. Once created, subsequent visits require logging in via `/admin/login`.

### Dashboard Features

- **System Overview (`/admin/dashboard`)**: Displays real-time aggregate counts for contacts, web commands, system commands, administrator accounts, database connectivity status, and AI service configuration state.
- **Contacts Management (`/admin/contacts`)**: Full CRUD interface for personal contacts. Validates international phone formats and optional email syntax. Seamlessly updates records used by WhatsApp voice automation.
- **Web Commands Management (`/admin/web-commands`)**: Full CRUD interface for browser shortcut commands. Validates URL syntax and rejects dangerous schemes (`javascript:`, `data:`, `file:`, `vbscript:`, etc.).
- **System Commands Management (`/admin/system-commands`)**: Full CRUD interface for Windows desktop applications. Strictly validates executable paths, rejecting shell metacharacters and command injection payloads. Offers a safe "Test Launch" feature via `os.startfile` (no `shell=True`).
- **Session Management & Logout (`/admin/logout`)**: Protected administrative views enforce server-side session checks with `HttpOnly` and `SameSite=Lax` cookies.

### Local-Only Security Model

- **Host Binding**: By default, the admin server binds strictly to `127.0.0.1` (localhost). It is not exposed to the local network or internet.
- **Defense in Depth**: Parameterized SQLite queries throughout prevent SQL injection. Input validators reject command injection and dangerous protocol schemes.
- **Secrets Protection**: Database files and `.env` credentials are never exposed via HTTP routes or client-side assets.

## Architecture

JARVIS follows a modular 4.x architecture where `app/` is the authoritative implementation layer and `engine/` acts as a compatibility and runtime bridge.

```text
       www/ (Eel Frontend)
             │
             ▼
     engine.command (Eel Bridge)
             │
             ▼
        app.routing (Command Dispatcher)
             │
             ▼
        app.services (Business Logic)
  ┌──────────┼──────────────┬─────────────┐
  ▼          ▼              ▼             ▼
System     Web           YouTube       WhatsApp
Apps       Commands       Search        Actions
  │          │              │             │
  └──────────┴──────────────┴─────────────┘
                    │
                    ▼
           OpenRouter Service
         (app.services.llm)
                    │
                    ▼
              Configured LLM
                    │
                    ▼
          app.speech (TTS/STT)
```

Core Layer Responsibilities:
- `app.config`: Authoritative configuration constants (`ASSISTANT_NAME`).
- `app.database`: Authoritative connection management, schema definitions, and idempotent seed routines.
- `app.routing`: Authoritative command intent classification and routing.
- `app.speech`: Authoritative speech recognition and text-to-speech engines.
- `app.services`: Independent domain services (LLM, system launcher, WhatsApp, YouTube).
- `app.admin`: Authoritative Phase 5 Admin Dashboard, authentication, and CRUD repositories.
- `engine/`: Compatibility wrappers and re-exports preserving public signatures and Eel interface contracts.
- `www/`: Static frontend assets (HTML, CSS, JavaScript) served via Eel.
- `run.py`: Multi-process entrypoint orchestrating the Eel UI, background Porcupine hotword listener, and local Admin Dashboard.

## Project Structure

```text
JARVIS/
├── app/
│   ├── admin/                   # Local Flask Admin Dashboard & management
│   │   ├── static/              # Local CSS & JavaScript assets
│   │   ├── templates/           # Server-rendered HTML dashboard templates
│   │   ├── auth.py              # Authentication, scrypt hashing & sessions
│   │   ├── routes.py            # HTTP & REST controller routes
│   │   ├── server.py            # Application factory & local WSGI runner
│   │   ├── services.py          # Repositories for contacts, web/sys commands
│   │   └── validators.py        # Input & security parameter validators
│   ├── core/
│   │   └── text_utils.py        # Text processing utilities
│   ├── database/
│   │   ├── connection.py        # Connection lifecycle management
│   │   ├── schema.py            # SQLite schema definitions
│   │   └── seed.py              # Default web command seed data
│   ├── routing/
│   │   └── router.py            # Central intent and command routing
│   ├── services/
│   │   ├── chat_history/        # Persistent conversation and message storage
│   │   ├── llm/
│   │   │   └── openrouter.py    # Authoritative OpenRouter API service
│   │   ├── system/
│   │   │   └── launcher.py      # System app and URL launcher
│   │   ├── whatsapp/
│   │   │   └── automation.py    # WhatsApp messaging and call automation
│   │   └── youtube/
│   │       └── player.py        # YouTube search and playback service
│   ├── speech/
│   │   ├── recognition.py       # Speech-to-text recognition
│   │   └── synthesis.py         # Text-to-speech audio synthesis
│   └── config.py                # Authoritative application configuration
├── engine/
│   ├── command.py               # Eel bridge and legacy command interface
│   ├── config.py                # Legacy config compatibility re-exports
│   ├── db.py                    # Legacy database compatibility re-exports
│   ├── features.py              # Legacy feature bridges and hotword listener
│   └── helper.py                # Legacy helper compatibility re-exports
├── www/
│   ├── assets/                  # Audio, icons, and vendor assets
│   ├── controller.js            # Frontend Eel controller
│   ├── index.html               # Main user interface page
│   ├── main.js                  # Frontend audio and UI interaction logic
│   ├── script.js                # Frontend animations and visual effects
│   └── style.css                # Interface styling
├── .env.example                 # Environment configuration template
├── .gitignore
├── main.py                      # Starts the Eel application process
├── run.py                       # Starts UI and hotword processes
├── requirements.txt             # Python dependencies
└── README.md
```

## OpenRouter Configuration

The authoritative LLM implementation resides in `app/services/llm/openrouter.py`. `engine/features.py` exposes a compatibility wrapper (`chatBot()`) that delegates directly to this service.

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
python -m unittest discover tests
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
