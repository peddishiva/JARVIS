# JARVIS System Baseline Validation Report

**Date:** October 5, 2026  
**Workspace:** `c:\Users\peddi\Desktop\Jarvis`  
**Validation Stage:** Step 2A — Current Application Baseline Validation  
**Source Code Baseline:** GitHub `main` branch (peddishiva/JARVIS)  
**Database File:** `jarvis.db` (SHA-256: `06a4a95523dac164a3a96ecf827a9845c0d9efa55632571bc2c8f755e61bad22`)  

---

## 1. Current Architecture

The baseline JARVIS application is a desktop voice assistant combining a local Python backend with an HTML/CSS/JavaScript graphical user interface served via **Eel** (a lightweight library combining Bottle web server and Gevent-WebSocket).

```
                      +---------------------------------------+
                      |         run.py (Multiprocessing)      |
                      +-------------------+-------------------+
                                          |
                     +--------------------+--------------------+
                     |                                         |
                     v                                         v
        +----------------------------+            +----------------------------+
        |  Process 1: startJarvis()  |            | Process 2: listenHotword() |
        +--------------+-------------+            +--------------+-------------+
                       |                                         |
     +-----------------+-----------------+                       |
     |                                   |                       |
     v                                   v                       |
+---------+                 +------------------------+           |
| Eel Web |                 |   Microsoft Edge App   |           |
| Server  |<================|   (localhost:8000)     |           |
+----+----+  WebSocket RPC  +-----------+------------+           |
     |                                  ^                        |
     v                                  |                        |
+------------------------------------+  |                        |
| engine.command.allCommands()       |  |                        |
|  - openCommand()                   |  |                        |
|  - PlayYoutube()                   |  |                        |
|  - findContact() / whatsApp()      |  |                        |
|  - chatBot() (OpenRouter API)      |  |                        |
+------------------+-----------------+  |                        |
                   |                    |                        |
                   |                    | PyAutoGUI Win+J Key    |
                   |                    +------------------------+
                   v
+------------------------------------+
| Hardware / System Integration      |
|  - SQLite (jarvis.db)              |
|  - pyttsx3 (SAPI5 TTS)             |
|  - SpeechRecognition (Google STT)  |
|  - PyAudio / Porcupine Hotword     |
+------------------------------------+
```

### Key Architectural Characteristics
- **Dual-Process Model:** Uses Python's `multiprocessing` to isolate hotword listening from the UI/Eel event loop.
- **Inter-Process Signaling via Keystroke Emulation:** When Process 2 detects a wake word, it uses PyAutoGUI to simulate a Windows shortcut (`Win + J`). The Eel browser window listens for `keyup` on `j + metaKey` and triggers `eel.allCommands()()`.
- **Eel Communication Bridge:** Python functions decorated with `@eel.expose` (`allCommands`, `playAssistantSound`) are callable from JavaScript; frontend functions (`DisplayMessage`, `ShowHood`, `senderText`, `receiverText`) are called from Python.
- **SQLite Data Layer:** Direct SQLite queries embedded directly within business logic modules.

---

## 2. Current Entry Points

| Entry Point | Implementation | Verified Behavior | Status |
| :--- | :--- | :--- | :--- |
| `run.py` | Spawns `p1` (`startJarvis()`) and `p2` (`listenHotword()`) using `multiprocessing.Process`. | Initializes Eel, plays assistant startup sound, starts Edge in app mode, and opens Porcupine audio stream in parallel. | **WORKING (with known process lifecycle caveats)** |
| `main.py` | Contains `def start():` with Eel initialization and Edge browser launch. | **Missing `if __name__ == '__main__':` block.** Executing `python main.py` exits immediately with returncode 0 without performing any action. | **NO-OP DEFECT** |
| `engine/db.py` | Top-level script connecting to `jarvis.db` with commented DDL/DML templates. | Connects to `jarvis.db` upon import at module root level. | **UTILITY SCRIPT ONLY** |

---

## 3. Current Command-Routing Flow

Command dispatch is centralized in `engine.command.allCommands(message=1)`:

```
allCommands(message=1)
   │
   ├── If message == 1:
   │       query = takecommand() [Google STT via SpeechRecognition]
   │       eel.senderText(query)
   │
   └── If message != 1:
           query = message [Typed from frontend UI]
           eel.senderText(query)
           [NOTE: query is NOT lowercased when message != 1]
   │
   ├── Rule 1: "open" in query
   │       └──> engine.features.openCommand(query)
   │               - Strips ASSISTANT_NAME and "open"
   │               - Checks sys_command in jarvis.db -> os.startfile()
   │               - Checks web_command in jarvis.db -> webbrowser.open()
   │               - Fallback: os.system("start " + query)
   │
   ├── Rule 2: "on youtube" in query
   │       └──> engine.features.PlayYoutube(query)
   │               - Extracts song via helper.extract_yt_term() regex
   │               - Launches browser via pywhatkit.playonyt()
   │
   ├── Rule 3: "send a message" in query OR "phone call" in query OR "video call" in query
   │       └──> engine.features.findContact(query)
   │               - Cleans stop words via helper.remove_words()
   │               - Looks up mobile_no from contacts table
   │               - Formats phone number with +91 prefix
   │       └──> engine.features.whatsApp(contact_no, query, message, name)
   │               - Launches whatsapp:// URL protocol via subprocess
   │               - Automates UI navigation using pyautogui.hotkey('tab') loops
   │
   └── Fallback: else
           └──> engine.features.chatBot(query)
                   - Sends prompt to OpenRouter completions API
                   - Speaks response via pyttsx3 and displays in UI
```

---

## 4. Database Behavior

- **Database File:** `jarvis.db`
- **File Integrity:** Verified read-only integrity before and after all baseline tests. SHA-256 remained constant:
  `06a4a95523dac164a3a96ecf827a9845c0d9efa55632571bc2c8f755e61bad22`
- **Schema & Data Audit:**

### `sys_command`
- **Columns:** `id INTEGER PRIMARY KEY`, `name VARCHAR(100)`, `path VARCHAR(1000)`
- **Record Count:** 1 row
- **Contents:**
  ```sql
  (1, 'onenote', 'C:\\Program Files\\Microsoft Office\\root\\Office16\\ONENOTE.EXE')
  ```

### `web_command`
- **Columns:** `id INTEGER PRIMARY KEY`, `name VARCHAR(100)`, `url VARCHAR(1000)`
- **Record Count:** 12 rows
- **Sample Records:**
  ```sql
  (1, 'canva', 'https://www.canva.com/')
  (2, 'youtube', 'https://www.youtube.com/')
  (3, 'amazon', 'https://www.amazon.in/')
  (4, 'flipkart', 'https://www.flipkart.com/')
  (5, 'myntra', 'https://www.myntra.com/')
  ...
  ```
  *(Note: Duplicate entry exists for 'youtube' in baseline data).*

### `contacts`
- **Columns:** `id INTEGER PRIMARY KEY`, `name VARCHAR(200)`, `mobile_no VARCHAR(255)`, `email VARCHAR(255) NULL`
- **Record Count:** 2 rows
- **Contents:**
  ```sql
  (1, 'shiva', '1234567890', NULL)
  (2, 'richard', '9347192033', NULL)
  ```

### Database Behavior Findings
- Lookup queries (`SELECT path FROM sys_command WHERE name IN (?)`, `SELECT url FROM web_command WHERE name IN (?)`, and `SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ?`) execute successfully.
- Relative path connection (`sqlite3.connect("jarvis.db")`) is executed at module load time in both `engine/db.py` and `engine/features.py`. If imported from a different working directory, a new empty database is created in the calling process's working directory.

---

## 5. OpenRouter Behavior

- **Client Configuration:** Implemented in `engine/features.py` using `openai.OpenAI(base_url="https://openrouter.ai/api/v1")`.
- **Configured Model:** `openrouter/free` (default).
- **Test Query:** Prompt: `"Respond with exactly: JARVIS_TEST_OK"`.
- **Result:**
  - Configured key in `.env` is the literal placeholder: `"your_openrouter_api_key_here"`.
  - The API call securely failed with `AuthenticationError: Error code: 401 - {'error': {'message': 'Missing Authentication header', 'code': 401}}`.
  - `chatBot()` caught `openai.AuthenticationError` and assigned `message = "The OpenRouter API key is invalid or expired."`.
  - Spoke fallback notification and delivered it to the UI via `eel.DisplayMessage()` and `eel.receiverText()`.
  - **Security check:** No API key was printed to stdout or logged to files.

---

## 6. Frontend / Eel Behavior

- **Web Server:** Eel v0.18.2 serving static assets from directory `www/`.
- **Frontend Stack:** HTML5, jQuery 3.6.0, Bootstrap 5.0.0, SiriWave, Textillate.
- **WebSocket RPC Verification:**
  - Automated test started Eel on localhost test port and connected a WebSocket client to `/eel?page=index.html`.
  - Successfully performed RFC 6455 WebSocket handshake upgrade (`HTTP/1.1 101 Switching Protocols`).
  - Dispatched simulated frontend call:
    `{"call": 1001, "name": "allCommands", "args": ["harmless baseline test"]}`
  - Verified 5 frames returned from Python over WebSocket:
    1. `senderText(["harmless baseline test"])`
    2. `DisplayMessage(["The OpenRouter API key is invalid or expired."])`
    3. `receiverText(["The OpenRouter API key is invalid or expired."])`
    4. `ShowHood([])`
    5. RPC return response `{"return": 1001, "status": "ok"}`
- **Result:** **PASS**. The frontend-to-Python bridge reaches Python and pushes updates back to the client.

---

## 7. Voice Pipeline

### A. Speech-to-Text (Input)
- **Library:** `SpeechRecognition` v3.17.0 with PyAudio v0.2.14.
- **Engine:** Google Web Speech API (`r.recognize_google(audio, language='en-in')`).
- **Hardware Detection:** PyAudio detected 24 audio endpoint drivers on Windows 11.
- **Default Capture Device:** Intel Smart Sound Technology Digital Microphone Array.
- **Ambient Noise Calibration:** `r.adjust_for_ambient_noise(source)` successfully measured ambient noise floor (energy threshold calibrated to ~121).
- **Limitation:** Hardcoded 10-second timeout and 6-second phrase limit (`r.listen(source, 10, 6)`). Requires internet connectivity.

### B. Text-to-Speech (Output)
- **Library:** `pyttsx3` v2.99 with Windows native `sapi5` driver.
- **Detected Voices:**
  - Index 0: `Microsoft David Desktop - English (United States)`
  - Index 1: `Microsoft Zira Desktop - English (United States)`
- **Configuration:** Set to David, rate = 174 wpm.
- **Verification:** Successfully executed speech synthesis without errors.

---

## 8. Hotword Pipeline

- **Engine:** Picovoice Porcupine v1.9.5 (`pvporcupine`).
- **Configured Wake Words:** `["jarvis", "alexa"]`.
- **Sample Rate:** 16,000 Hz.
- **Buffer Frame Length:** 512 samples.
- **Audio Stream:** PyAudio 16-bit mono input stream matching Porcupine parameters.
- **Automated Verification:** Verified initialization, stream opening, unpacking PCM buffers (`h*512`), and frame processing loop for 5 frames without overflow.
- **Wake Word Action:** Emulates `Win + J` via PyAutoGUI.
- **Architecture Risk:** Requires the Edge application window to have foreground focus; does not work if another window consumes global hotkeys.

---

## 9. WhatsApp Pipeline

- **Function:** `engine.features.whatsApp(mobile_no, message, flag, name)`
- **URL Scheme:** `whatsapp://send?phone={mobile_no}&text={encoded_message}` launched via Windows `start` command.
- **Navigation Automation:**
  - Sleeps 5 seconds for WhatsApp Desktop to load.
  - Sends `Ctrl + F` followed by repeated `Tab` presses:
    - Message: 19 tabs
    - Voice call: 14 tabs
    - Video call: 13 tabs
  - Sends `Enter`.
- **Validation Results:**
  - Parsing and contact lookup: Verified working against `jarvis.db` (`shiva` -> `+911234567890`).
  - URL encoding: Correctly uses `urllib.parse.quote`.
  - Automation Risk: Extremely fragile. UI updates to WhatsApp Desktop alter the tab ordering, leading to misdirected clicks or failed calls.

---

## 10. What Was Successfully Automated

1. **Database Integrity & Schema Audit:** Verified tables, row counts, and read-only hash retention.
2. **Command Routing Logic:** Verified simulated dispatch across all 6 command categories.
3. **OpenRouter API Verification:** Tested real network call, confirmed model configuration, verified 401 handling without exposing keys.
4. **Eel WebSocket Bridge:** Tested end-to-end bi-directional RPC over raw WebSocket protocol.
5. **TTS Audio Output:** Verified SAPI5 engine initialization, voice selection, and speech synthesis.
6. **Microphone Hardware Verification:** Verified PyAudio device discovery and SpeechRecognition ambient noise calibration.
7. **Porcupine Wake Word Engine:** Verified engine creation, audio buffer processing, and clean shutdown.
8. **Automation Command Parsing:** Verified YouTube regex extraction, stop-word removal, and WhatsApp URL formation.
9. **Launcher Lifecycle Verification:** Tested `python main.py` (discovered missing `__main__`) and `python run.py` (verified multiprocessing spawn).

---

## 11. What Requires Manual Testing

1. **Human Spoken Voice Input:** Testing actual voice capture through Google STT with human speech.
2. **Real-time Hotword Detection:** Speaking "Jarvis" or "Alexa" aloud to verify that the PyAutoGUI keystroke activates the SiriWave UI.
3. **WhatsApp Desktop Automation:** Verifying tab navigation with active WhatsApp Desktop installed and logged in.
4. **YouTube Playback Launch:** Verifying `pywhatkit.playonyt` launches a browser tab with playback.
5. **System Application Launch:** Verifying `os.startfile` launches Microsoft OneNote from the configured path.

---

## 12. Known Bugs and Deficiencies

1. **`main.py` is a No-Op:** Missing `if __name__ == '__main__': start()`. Running `python main.py` exits immediately.
2. **Case Sensitivity Defect in Text Input:** In `allCommands(message=1)`, when `message != 1`, `query` is assigned without `.lower()`. Commands like `"Open notepad"` or `"Play ... on youtube"` fail pattern matching.
3. **Spelling Typo in Stop Words:** `words_to_remove` in `findContact()` contains `'wahtsapp'` instead of `'whatsapp'`. Saying "send a whatsapp message to shiva" fails to match contact "shiva".
4. **Crash on Unmatched YouTube Queries:** If a query contains `"on youtube"` but does not match `r'play\s+(.*?)\s+on\s+youtube'`, `extract_yt_term()` returns `None`. `PlayYoutube` attempts string concatenation `"Playing " + None`, raising an unhandled `TypeError`.
5. **No-Op `lower()` Call in `openCommand`:** Line 57 has `query.lower()` without assignment (`query = query.lower()`), leaving uppercase letters intact.
6. **Forced Voice Prompt during Text WhatsApp Command:** When typing `"send a message to shiva"` in the chat box, `allCommands` forces `query = takecommand()`, blocking on the microphone even for typed requests.
7. **Eel Attribute Errors When Uninitialized:** `engine/command.py` calls `eel.senderText()` and `eel.ShowHood()`. If imported before `eel.init('www')` is called, Eel raises `AttributeError: module 'eel' has no attribute 'senderText'`.
8. **Relative Database Path:** `sqlite3.connect("jarvis.db")` opens relative to `os.getcwd()` rather than the project root directory.
9. **Silent Exception Swallowing:** `allCommands()` wraps routing in a bare `except: print("error")`, obscuring root causes and tracebacks.

---

## 13. Technical Debt

- **Hardcoded GUI Tab Automation:** WhatsApp integration depends on fixed keystroke counts (13, 14, 19 tabs) that break across app versions.
- **PyAutoGUI Keystroke Emulation as IPC:** Using synthetic `Win + J` keystrokes to bridge background processes to the frontend is fragile and interferes with user desktop activities.
- **Multiple Unmanaged Database Connections:** Both `engine/db.py` and `engine/features.py` open separate SQLite connections at import time without connection pooling or context managers.
- **Missing Structured Intent System:** Dispatch relies on naive substring searches (`"open" in query`, `"on youtube" in query`), creating routing conflicts (e.g., "open youtube" matches `openCommand` before `PlayYoutube`).
- **No Conversation Memory:** Each OpenRouter query is treated as an isolated, single-turn interaction without history or context.

---

## 14. Recommended Implementation Order for Future Development

1. **Phase 1: Robust Database Initialization & Schema Layer (`engine/db_init.py`)**
   - Resolve absolute database pathing relative to repository root.
   - Implement idempotent table creation (`CREATE TABLE IF NOT EXISTS`).
   - Implement seed data and connection context managers.
2. **Phase 2: Configuration & Environment Hardening**
   - Centralize configuration in `engine/config.py` with validated environment variables.
   - Graceful handling of missing or placeholder API keys.
3. **Phase 3: Core Command & Intent Dispatch Refactoring**
   - Standardize input normalization (`.strip().lower()`) for both text and voice.
   - Implement structured intent parser to eliminate substring collisions.
   - Replace bare `except:` clauses with structured error logging.
4. **Phase 4: Entry Point & Launcher Stabilization**
   - Fix `main.py` entry point (`if __name__ == '__main__': start()`).
   - Replace PyAutoGUI `Win+J` IPC with clean inter-process queues or direct Eel events.
   - Implement clean shutdown signals for multiprocessing workers.
5. **Phase 5: Conversational Memory & AI Enhancement**
   - Introduce multi-turn conversation memory for `chatBot()`.
   - Implement token management and assistant persona rules.
6. **Phase 6: Windows Automation & External Service Hardening**
   - Fix `extract_yt_term` regex and fallback handling.
   - Modernize WhatsApp dispatch or provide graceful status feedback.
   - Fix `findContact` typo (`'wahtsapp'`).

---

## Subsystem Baseline Validation Summary

| Subsystem | Baseline Status | Notes / Root Cause |
| :--- | :--- | :--- |
| **Database (`jarvis.db`)** | **PASS** | Connection works; all 3 tables exist; lookups succeed; 0 writes made. |
| **Command Routing** | **PASS (with known logic bugs)** | Routing executes; logic contains case-sensitivity and regex edge cases. |
| **OpenRouter Client** | **PASS (Network/Client) / BLOCKED (API Key)** | OpenAI client works; placeholder key produces expected 401; safely handled. |
| **Eel Frontend-to-Python Bridge** | **PASS** | WebSocket RPC reaches Python and returns 5 UI update frames. |
| **Voice Pipeline (TTS)** | **PASS** | pyttsx3 / SAPI5 initializes David voice and synthesizes speech. |
| **Voice Pipeline (STT)** | **PASS (Hardware) / MANUAL (Speech)** | PyAudio mic opened, calibrated; human speech recognition requires manual test. |
| **Hotword Pipeline** | **PASS (Engine) / MANUAL (Acoustic)** | Porcupine 1.9.5 initializes, streams 512-sample PCM; keyword test requires manual voice. |
| **Launcher (`main.py`)** | **FAIL** | Missing `__main__` caller; exits immediately with returncode 0. |
| **Launcher (`run.py`)** | **PASS (Execution) / FRAGILE (IPC)** | Starts both processes; relies on PyAutoGUI `Win+J` emulation. |
| **Windows Automation** | **PASS (Dry-Run) / MANUAL (Live)** | Contact lookup, URL encoding work; live tab navigation requires manual verification. |
