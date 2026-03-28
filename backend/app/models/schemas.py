from pydantic import BaseModel
from typing import Optional, Literal


# ─── Client → Server ────────────────────────────────────────────────────────

class AudioConfig(BaseModel):
    """First message sent by client to configure the session."""
    type: Literal["config"] = "config"
    language_code: str = "hi-IN"          # e.g. hi-IN, es-ES, gu-IN, en-US
    target_language: str = "en"           # e.g. en, es, hi
    sample_rate: int = 16000
    auto_detect: bool = False              # if True, backend detects language


# ─── Server → Client ────────────────────────────────────────────────────────

class TranscriptEvent(BaseModel):
    """Emitted for every interim and final STT result."""
    type: Literal["transcript"] = "transcript"
    text: str
    is_final: bool
    language: str                          # detected or configured language code
    confidence: Optional[float] = None


class TranslationEvent(BaseModel):
    """Emitted for both interim and final translation results."""
    type: Literal["translation"] = "translation"
    original: str
    translated: str
    source_language: str
    target_language: str = "en"
    is_final: bool = True


class TTSAudioEvent(BaseModel):
    """Bonus: synthesized English speech as base64-encoded MP3."""
    type: Literal["tts_audio"] = "tts_audio"
    audio_base64: str
    format: str = "mp3"


class ErrorEvent(BaseModel):
    """Emitted when any Google API call fails."""
    type: Literal["error"] = "error"
    message: str
    code: Optional[str] = None


class StatusEvent(BaseModel):
    """Connection / session lifecycle updates."""
    type: Literal["status"] = "status"
    state: Literal["connected", "listening", "idle", "disconnected"]
    message: Optional[str] = None
