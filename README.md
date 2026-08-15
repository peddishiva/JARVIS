# JARVIS

A Windows-first Python desktop voice assistant with a local web UI. JARVIS combines speech recognition, text-to-speech, hotword detection, desktop/web app launching, YouTube playback, WhatsApp automation, SQLite-backed contacts/commands, and an AI chatbot powered through HuggingChat.

## Features

- Voice input using `SpeechRecognition` and the system microphone.
- Voice output using `pyttsx3` with the Windows SAPI5 speech engine.
- Wake-word detection for **JARVIS** / **Alexa** using Picovoice Porcupine.
- Browser-style desktop UI built with **Eel**, served from the `www/` directory.
- Opens Windows applications and registered web commands from SQLite.
- Plays YouTube searches through `pywhatkit`.
- Sends WhatsApp messages and starts WhatsApp calls/video calls using Windows URL/developer automation.
- AI chat responses through `hugchat`, using the repository's `engine/cookies.json` session data.
- Local SQLite database support for commands and contacts.

## Requirements

JARVIS is currently designed for **Windows**. The source starts Microsoft Edge in app mode and uses Windows-specific APIs such as SAPI5 and `os.startfile`.

Recommended environment:

- Windows 10/11
- Python 3.10+ (the repository contains Python 3.12 bytecode, so Python 3.12 is a reasonable choice)
- Working microphone
- Speakers/headphones
- Microsoft Edge
- WhatsApp Desktop or a Windows environment capable of opening `whatsapp://` links

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/peddishiva/JARVIS.git
cd JARVIS
```

### 2. Create a virtual environment

```powershell
python -m venv venv
```

Activate it in PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution for the current session, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 3. Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### 4. Install Python dependencies

The current repository does not include a `requirements.txt`, so install the dependencies used by the source code:

```powershell
pip install eel pyttsx3 SpeechRecognition PyAudio pywhatkit pyautogui pygame pvporcupine==1.9.5 hugchat
```

Notes:

- `webbrowser`, `sqlite3`, `subprocess`, `multiprocessing`, `os`, `sys`, `time`, `struct`, and `urllib.parse` are part of Python's standard library and do not need separate installation.
- `PyAudio` provides microphone access for the speech-recognition and Porcupine paths.
- If `pygame` installation fails, upgrade pip first and retry.
- The project currently imports `pvporcupine` with the legacy `keywords=["jarvis", "alexa"]` API, so the pinned `1.9.5` version is intentional.

### 5. Verify the AI chatbot session

The chatbot initializes HuggingChat using:

```text
engine/cookies.json
```

The application expects this session data to be available. Do not publish your personal HuggingChat cookies or replace the tracked file with private credentials. If the existing session is invalid, recreate the HuggingChat authentication/session data using a safe local copy and keep secrets out of Git.

### 6. Start JARVIS

For the normal dual-process launcher:

```powershell
python run.py
```

`run.py` starts the Eel UI and the hotword listener as separate processes. fileciteturn4file0

You can also start the UI directly:

```powershell
python main.py
```

`main.py` initializes the `www/` Eel web app, plays the startup sound, and opens Microsoft Edge at `http://localhost:8000/index.html` in app mode. fileciteturn3file0

## How It Works

```text
Microphone
   │
   ▼
Hotword Listener (Porcupine)
   │
   └── detects "Jarvis" / "Alexa"
           │
           ▼
        Win + J
           │
           ▼
      Eel Web Interface
           │
           ▼
    SpeechRecognition
           │
           ▼
       Command Router
        ┌────┼───────────────┬──────────────┐
        ▼    ▼               ▼              ▼
     System Web          YouTube        WhatsApp
     Commands Commands      Search        Actions
        │    │               │              │
        └────┴───────────────┴──────────────┘
                         │
                         ▼
                    HuggingChat AI
                         │
                         ▼
                    pyttsx3 / SAPI5
```

The command router recognizes requests such as `open ...`, YouTube requests, WhatsApp message/call/video-call requests, and sends other text to the chatbot. fileciteturn6file0

## Project Structure

```text
JARVIS/
├── engine/
│   ├── command.py       # Speech recognition and command routing
│   ├── config.py        # Assistant name configuration
│   ├── cookies.json     # HuggingChat session/cookie data
│   ├── db.py            # SQLite schema/data helper code
│   ├── features.py      # Hotword, app, web, YouTube, WhatsApp and AI features
│   └── helper.py        # Text/YouTube helper functions
├── www/
│   ├── assets/          # Audio, icon and vendor assets
│   ├── controller.js
│   ├── index.html       # Eel UI entry page
│   ├── main.js
│   ├── script.js
│   └── style.css
├── main.py              # Starts the Eel application
├── run.py               # Starts UI + hotword listener processes
├── commands Used.txt    # Original setup/command notes
└── README.md
```

## Database Setup

JARVIS uses a local SQLite file named `jarvis.db`. The code expects tables for:

- `sys_command` — maps a command name to a Windows executable path.
- `web_command` — maps a command name to a web URL.
- `contacts` — stores contact names and mobile numbers used by WhatsApp automation.

The database helper code documents example SQL for creating/populating these tables in `engine/db.py`. fileciteturn9file0

Because the application opens `jarvis.db` directly, place the database in the project root or initialize the tables before using database-backed commands.

## Customization

### Change the assistant name

Edit `engine/config.py`:

```python
ASSISTANT_NAME = "jarvis"
```

The current configuration uses `jarvis`. fileciteturn8file0

### Add applications or websites

Use the SQLite tables described in `engine/db.py` to register desktop applications and web commands. For example, a system command stores an application name and its Windows executable path, while a web command stores a name and URL. fileciteturn9file0

### Add contacts

The WhatsApp feature looks up contacts by name in the `contacts` table and expects a mobile number. The current implementation automatically adds the `+91` country prefix when a number does not already start with it. fileciteturn5file0

## Example Commands

Try commands such as:

```text
Open YouTube
Open Notepad
Play Believer on YouTube
Send a message to Shiva
Phone call to Shiva
Video call to Shiva
What is machine learning?
```

The exact available application names depend on entries in your `jarvis.db` database.

## Troubleshooting

### `ModuleNotFoundError`

Make sure the virtual environment is active and reinstall the dependency:

```powershell
.\venv\Scripts\Activate.ps1
pip install <package-name>
```

### PyAudio installation fails

Confirm you are using a supported Windows/Python combination and that pip is up to date:

```powershell
python -m pip install --upgrade pip
pip install PyAudio
```

### Microphone does not work

Check Windows microphone permissions, confirm the correct input device is selected, and test the microphone with another application.

### JARVIS starts but Edge does not open

The launcher explicitly invokes `msedge.exe`, so Microsoft Edge must be installed and available through the Windows command path. fileciteturn3file0

### Hotword detection does not start

The hotword listener uses Porcupine and PyAudio, and the code opens the default microphone stream. Check microphone permissions and confirm `pvporcupine` and `PyAudio` are installed. fileciteturn5file0

### WhatsApp automation fails

The current implementation relies on Windows `whatsapp://send?...` links plus keyboard automation with `pyautogui`. Make sure WhatsApp is installed/configured and that the target contact exists in the local database. fileciteturn5file0

### AI chatbot does not respond

The chatbot creates a HuggingChat client from `engine/cookies.json`. An expired or invalid session file will prevent authenticated chatbot use. fileciteturn5file0

## Security Notes

- Treat `engine/cookies.json` as sensitive authentication material. Rotate/remove it if it contains an exposed personal session.
- Do not commit passwords, API keys, authentication cookies, or personal contacts.
- Review the contents of `jarvis.db` before publishing the repository if it contains real phone numbers or other personal information.
- JARVIS can launch applications and automate external services, so only run commands you trust.

## Development Commands

```powershell
# Activate environment
.\venv\Scripts\Activate.ps1

# Run the complete assistant
python run.py

# Run the UI launcher directly
python main.py

# Deactivate environment
deactivate
```

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Test the change on Windows.
4. Keep credentials and personal data out of commits.
5. Open a pull request with a clear description of the change.

## License

No license file is currently present in the repository. Unless a license is added, the source should not be assumed to be available for unrestricted reuse, redistribution, or modification.

## Acknowledgements

JARVIS is built with open-source Python and web technologies including Eel, PyAudio, SpeechRecognition, pyttsx3, pygame, PyAutoGUI, PyWhatKit, Picovoice Porcupine, HuggingChat, SQLite, HTML, CSS, and JavaScript.
