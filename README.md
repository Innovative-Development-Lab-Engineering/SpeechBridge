# SpeechBridge

Real-time multilingual speech transcription and translation. Speak in one language, read and hear it instantly in another.

Supports **English, Hindi, Spanish, and Gujarati** in any direction.

---

## How it works

```
Microphone → WebSocket → Google STT → Google Translate / Gemini → WebSocket → Browser
                                                                              ↓
                                                              Transcript + Translation + TTS
```

1. The browser captures microphone audio and streams raw PCM chunks over a WebSocket
2. The backend feeds audio into Google Cloud Speech-to-Text (streaming, with interim results)
3. Each transcript (interim and final) is forwarded to the client immediately
4. Final transcripts are translated using Gemini with context from recent sentences
5. Interim transcripts are translated using Google Cloud Translation API (fast path)
6. Translated text is spoken aloud in the browser using the Web Speech API

---

## Features

- Real-time streaming transcription with interim results
- Language auto-detection via `alternative_language_codes` (handles code-switching)
- Context-aware translation — uses the last 3 sentences to improve accuracy
- Browser TTS reads translated text aloud (accessibility)
- Full conversation history visible for both original and translated text
- Google ADK agent with 4 skills: transcribe, detect language, translate, synthesize speech

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite 4 |
| Backend | FastAPI, Python 3.11, uvicorn |
| Speech-to-Text | Google Cloud Speech-to-Text v1 (streaming) |
| Translation | Google Cloud Translation API v2 + Gemini |
| Text-to-Speech | Google Cloud Text-to-Speech + Browser Web Speech API |
| Agent | Google ADK (Agent Development Kit) |
| Transport | WebSockets (binary PCM audio + JSON events) |

---

## Project Structure

```
SpeechBridge/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, lifespan
│   │   ├── api/
│   │   │   └── websocket.py         # /ws/translate — core streaming endpoint
│   │   ├── agent/
│   │   │   ├── agent.py             # Google ADK agent definition (Gemini)
│   │   │   └── skills/
│   │   │       ├── transcribe_skill.py   # STT configuration skill
│   │   │       ├── translate_skill.py    # Translation skill
│   │   │       ├── detect_lang_skill.py  # Language detection skill
│   │   │       └── tts_skill.py          # Text-to-speech skill
│   │   ├── services/
│   │   │   ├── speech_service.py    # Google STT streaming wrapper
│   │   │   └── translation_service.py   # Google Translate wrapper + cache
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic WebSocket message schemas
│   │   ├── config/
│   │   │   └── settings.py          # Pydantic settings (loads from .env)
│   │   └── utils/
│   │       └── logger.py            # Structured logging
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Root component, state management
│   │   ├── components/
│   │   │   ├── MicButton.jsx        # Record / stop toggle
│   │   │   ├── LanguageSelector.jsx # Source language dropdown
│   │   │   ├── TranscriptDisplay.jsx  # Original language panel
│   │   │   ├── TranslationDisplay.jsx # Translated text panel
│   │   │   └── StatusBar.jsx        # Connection + error status
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js      # WS lifecycle, message routing
│   │   │   └── useAudioStream.js    # Microphone capture, PCM streaming
│   │   └── services/
│   │       └── websocketService.js  # WS URL, config/stop message helpers
│   ├── vite.config.js               # Vite + WS proxy to backend
│   └── package.json
└── stt.json                         # Google service account key (not committed)
```

---

## Prerequisites

- Python 3.11+
- Node.js 16+
- A Google Cloud project with the following APIs enabled:
  - Cloud Speech-to-Text API
  - Cloud Translation API
  - Cloud Text-to-Speech API
- A Google service account key with access to the above APIs
- A Google AI Studio API key (for Gemini / ADK)

---

## Setup

### 1. Clone and configure

```bash
git clone <repo-url>
cd SpeechBridge
```

Place your Google service account JSON file at:
```
SpeechBridge/stt.json
```

### 2. Backend

```bash
cd backend
cp .env.example .env
```

Edit `.env` and set your Gemini API key:
```
GOOGLE_API_KEY=your_key_from_aistudio.google.com
```

Install dependencies (use your Python 3.11+ virtualenv):
```bash
pip install -r requirements.txt
```

Start the backend:
```bash
GOOGLE_APPLICATION_CREDENTIALS="C:/path/to/SpeechBridge/stt.json" \
  uvicorn app.main:app --port 8000
```

> **Note:** The `GOOGLE_APPLICATION_CREDENTIALS` env var must be set in the shell before starting — not just in `.env` — because some Google client libraries initialize before the app reads `.env`.

Verify:
```bash
curl http://localhost:8000/health
# {"status":"ok","service":"speech-translation-api","version":"1.0.0"}
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Environment Variables

All backend config lives in `backend/.env`. See `backend/.env.example` for the full list.

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | `../stt.json` | Path to service account key |
| `GCP_PROJECT_ID` | `nyuhackathon` | Google Cloud project ID |
| `GOOGLE_API_KEY` | *(required)* | Gemini API key from AI Studio |
| `GOOGLE_GENAI_USE_VERTEXAI` | `false` | Set `true` to use Vertex AI instead of AI Studio |
| `DEFAULT_TARGET_LANGUAGE` | `en` | Fallback target language |
| `SUPPORTED_LANGUAGES` | `en-US,hi-IN,es-ES,gu-IN` | Comma-separated BCP-47 codes |
| `BACKEND_HOST` | `0.0.0.0` | Server bind host |
| `BACKEND_PORT` | `8000` | Server port |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed frontend origins |
| `AUDIO_SAMPLE_RATE` | `16000` | PCM sample rate in Hz |
| `AUDIO_CHUNK_SIZE` | `1600` | PCM chunk size in samples |

---

## WebSocket Protocol

Connect to `ws://localhost:8000/ws/translate`

### Message flow

```
Client                              Server
  |                                   |
  |<-- {"type":"status","state":"connected"} --------|
  |                                   |
  |--> {"type":"config", ...} ------->|
  |                                   |
  |<-- {"type":"status","state":"listening"} --------|
  |                                   |
  |--> [binary PCM audio chunk] ----->|  (repeat)
  |                                   |
  |<-- {"type":"transcript", ...} ----|  (interim + final)
  |<-- {"type":"translation", ...} ---|  (interim + final)
  |                                   |
  |--> {"type":"stop"} -------------->|
  |                                   |
  |<-- {"type":"status","state":"disconnected"} -----|
```

### AudioConfig (first message, JSON)

```json
{
  "type": "config",
  "language_code": "hi-IN",
  "target_language": "en",
  "sample_rate": 16000,
  "auto_detect": false
}
```

### Server events

| Type | Key fields |
|------|-----------|
| `status` | `state`: `connected` \| `listening` \| `disconnected` |
| `transcript` | `text`, `is_final`, `language`, `confidence` |
| `translation` | `original`, `translated`, `source_language`, `target_language`, `is_final` |
| `tts_audio` | `audio_base64` (MP3), `format` |
| `error` | `message` |

---

## Docker

```bash
cd backend
docker build -t speechbridge-backend .
docker run -p 8000:8000 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/stt.json \
  -e GOOGLE_API_KEY=your_key \
  -v $(pwd)/../stt.json:/app/stt.json \
  speechbridge-backend
```

---

## Supported Languages

| Language | BCP-47 Code | Target Code |
|----------|-------------|-------------|
| English | `en-US` | `en` |
| Hindi | `hi-IN` | `hi` |
| Spanish | `es-ES` | `es` |
| Gujarati | `gu-IN` | `gu` |

Translation works in any direction between these four languages.

---

## Testing

### Health check
```bash
curl http://localhost:8000/health
curl http://localhost:8000/info
```

### WebSocket (no microphone needed)
```python
# test_ws.py
import asyncio, json, websockets

async def test():
    async with websockets.connect("ws://localhost:8000/ws/translate") as ws:
        print(await ws.recv())  # connected
        await ws.send(json.dumps({
            "type": "config", "language_code": "hi-IN",
            "target_language": "en", "sample_rate": 16000,
        }))
        print(await ws.recv())  # listening
        await ws.send(b'\x00\x00' * 16000)  # 1s silence
        await ws.send(json.dumps({"type": "stop"}))
        try:
            while True:
                print(await asyncio.wait_for(ws.recv(), timeout=3.0))
        except asyncio.TimeoutError:
            pass

asyncio.run(test())
```

### Translation service in isolation
```python
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../stt.json"
from app.services.translation_service import TranslationService

svc = TranslationService()
print(svc.translate("नमस्ते", source_lang="hi-IN", target_lang="en"))
```
