# English Voice Coach AI

A voice-based English conversation coach with AI-powered correction and SQLite conversation history.

[Ler em português](README.pt-BR.md) · [Back to language selector](README.md)

---

## About the project

**English Voice Coach AI** is a Python project designed to help English learners practice spoken conversation using their computer microphone.

The core idea is simple: the user speaks in English, the system transcribes the audio, an AI coach corrects the sentence, suggests more natural alternatives and keeps the conversation going with a follow-up question in English.

The MVP was designed to be useful, affordable to run and portfolio-friendly. For that reason, the AI coach responds as text in the terminal instead of generating spoken audio. The practice is still voice-based because the user answers by speaking into the microphone.

---

## MVP flow

```text
User speaks through the microphone
↓
Manual recording controlled with Enter
↓
Audio transcription with OpenAI
↓
AI coach corrects the sentence
↓
Coach shows suggestions and a text response
↓
Coach asks a related follow-up question
↓
Conversation turn is saved in SQLite
↓
User answers again by speaking
```

---

## Key product decisions

### 1. Manual recording with Enter

The system does not automatically stop recording after a few seconds of silence. This decision was made because English learners often need time to think before finishing an answer.

The recommended flow is:

```text
Press Enter to start recording.
Speak at your own pace.
Press Enter again to stop recording.
```

### 2. No required TTS in the MVP

The project does not require AI voice output in the first version. The teacher response is displayed as text in the terminal.

This keeps the project cheaper to run, reduces audio playback complexity and keeps the focus on the main goal: spoken English practice with correction and conversation continuity.

### 3. Separate conversation sessions

Each app execution creates a new conversation session.

```text
Today: python run.py → session 1
Tomorrow: python run.py → session 2
```

Previous conversations remain stored in the database, but the coach only receives recent context from the current session. This prevents a new conversation from being mixed with topics from previous days.

### 4. One final follow-up question per turn

The interface shows the teacher response and the continuation question in the same block. The coach should avoid asking one question inside the main answer and another one separately.

Expected format:

```text
Teacher response:
Programming sounds like a great way to spend your time.

What kind of software do you like to create?
```

---

## Features

- Microphone audio capture.
- Manual start/stop recording controlled by the user.
- Audio transcription with the OpenAI API.
- Grammar correction and naturalness improvement.
- Alternative sentence suggestions.
- Conversational response in English.
- Final follow-up question to encourage the user to keep speaking.
- AI response validation with Pydantic.
- Rich terminal interface.
- Persistent SQLite history.
- Separate sessions for different conversations.
- Ruff linting and formatting.
- Automated tests with `unittest`.

---

## Tech stack

- Python 3.11+
- OpenAI API
- python-dotenv
- sounddevice
- soundfile
- numpy
- Pydantic
- Rich
- SQLite
- Ruff
- unittest

---

## Architecture

```text
english-voice-coach/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── audio/
│   │   ├── recorder.py
│   │   ├── player.py
│   │   └── silence_detector.py
│   ├── ai/
│   │   ├── transcriber.py
│   │   └── coach.py
│   ├── storage/
│   │   ├── database.py
│   │   └── repository.py
│   ├── ui/
│   │   └── terminal_ui.py
│   └── prompts/
│       └── english_coach_prompt.py
├── data/
│   └── audio/
├── docs/
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── README.md
├── README.pt-BR.md
├── README.en.md
└── run.py
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/english-voice-coach.git
cd english-voice-coach
```

### 2. Create and activate the virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=your_key_here
APP_LANGUAGE=pt-BR
COACH_LEVEL=intermediate
SAMPLE_RATE=16000
SILENCE_THRESHOLD=0.01
SILENCE_DURATION_MS=1500
DB_PATH=data/conversations.db
AUDIO_TEMP_DIR=data/audio
RECORDING_MODE=manual
TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
COACH_MODEL=gpt-4.1-mini
ENABLE_TTS=false
```

> Never commit your `.env` file to GitHub. Only `.env.example` should be versioned.

---

## Running the app

```bash
python run.py
```

Expected flow:

```text
1. The app creates a new session.
2. You press Enter to start recording.
3. You speak in English.
4. You press Enter again to stop recording.
5. The audio is transcribed.
6. The coach corrects and responds in text.
7. The turn is saved in the database.
8. You answer the next question by speaking again.
```

To exit:

```text
exit
```

---

## Validating SQLite

Initialize the database:

```powershell
python -c "from app.storage.database import initialize_database; initialize_database(); print('Database initialized successfully.')"
```

Check tables in PowerShell:

```powershell
python -c "import sqlite3; con = sqlite3.connect('data/conversations.db'); print(con.execute('SELECT name FROM sqlite_master WHERE type = ?', ('table',)).fetchall()); con.close()"
```

Expected result:

```text
[('conversation_sessions',), ('conversations',)]
```

---

## Tests

Run all tests:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## Ruff

Check lint errors:

```bash
ruff check .
```

Automatically fix what Ruff can fix:

```bash
ruff check . --fix
```

Format code:

```bash
ruff format .
```

Check formatting without changing files:

```bash
ruff format . --check
```

---

## Roadmap

- Add optional TTS mode.
- Generate automatic session summaries.
- Add user progress statistics.
- Support different coach strictness levels.
- Export conversation history to Markdown or CSV.
- Build a web interface in the future.

---

## Portfolio value

This project demonstrates experience with:

- AI API integration;
- audio processing;
- modular Python architecture;
- Pydantic data validation;
- SQLite persistence;
- terminal UI with Rich;
- Ruff-based code quality workflow;
- incremental technical documentation;
- product decisions based on cost, usability and maintainability.

---

## License

This project can be used as a learning and portfolio project. Define a formal license before publishing it for production use.
