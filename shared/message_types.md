# WebSocket Message Protocol

## Overview
All messages are JSON (text frames), except audio which is binary frames.

---

## Client → Server

### 1. AudioConfig (first message, text frame)
```json
{
  "type": "config",
  "language_code": "hi-IN",
  "sample_rate": 16000,
  "auto_detect": false
}
```
**Fields:**
- `language_code`: BCP-47. One of: `hi-IN`, `es-ES`, `en-US`
- `sample_rate`: Must be `16000`
- `auto_detect`: If `true`, backend runs language detection skill first

### 2. Audio Chunks (binary frames)
- Format: LINEAR16 PCM
- Sample rate: 16000 Hz
- Channels: 1 (mono)
- Chunk size: 1600–4096 samples

### 3. Stop Signal (text frame)
```json
{ "type": "stop" }
```

### 4. Enable TTS (text frame)
```json
{ "type": "enable_tts" }
```

---

## Server → Client

### 1. StatusEvent
```json
{
  "type": "status",
  "state": "connected | listening | idle | disconnected",
  "message": "Human-readable description"
}
```

### 2. TranscriptEvent
```json
{
  "type": "transcript",
  "text": "नमस्ते दुनिया",
  "is_final": true,
  "language": "hi-IN",
  "confidence": 0.97
}
```
- Emitted for **both interim and final** results
- `confidence` is only non-null when `is_final: true`

### 3. TranslationEvent
```json
{
  "type": "translation",
  "original": "नमस्ते दुनिया",
  "translated": "Hello World",
  "source_language": "hi-IN",
  "target_language": "en",
  "is_final": true
}
```
- Only emitted when `is_final: true` from STT

### 4. TTSAudioEvent (optional, if TTS enabled)
```json
{
  "type": "tts_audio",
  "audio_base64": "<base64-encoded MP3>",
  "format": "mp3"
}
```

### 5. ErrorEvent
```json
{
  "type": "error",
  "message": "STT quota exceeded",
  "code": "RESOURCE_EXHAUSTED"
}
```

---

## Session Lifecycle

```
Client                            Server
  │──── WebSocket Connect ──────────▶│
  │◀─── StatusEvent(connected) ──────│
  │──── AudioConfig JSON ───────────▶│
  │◀─── StatusEvent(listening) ──────│
  │──── [binary PCM chunks...] ─────▶│
  │◀─── TranscriptEvent(interim) ────│  (every ~200ms)
  │◀─── TranscriptEvent(final) ──────│
  │◀─── TranslationEvent ────────────│  (on final only)
  │◀─── TTSAudioEvent ───────────────│  (if TTS enabled)
  │──── { type: "stop" } ───────────▶│
  │◀─── StatusEvent(disconnected) ───│
  └──── WebSocket Close ─────────────┘
```
