"""
Transcribe Skill — ADK Tool wrapping Google Cloud Speech-to-Text.
Used by the translation_agent to transcribe audio bytes.
"""

from google.adk.tools import FunctionTool
from app.services.speech_service import SpeechService

_speech_service = SpeechService()


def transcribe_audio(language_code: str = "hi-IN") -> dict:
    """
    ADK Skill: Transcribe live audio input using Google Cloud STT.

    This skill is called by the agent to initiate a streaming transcription
    session. In agent context, it signals the pipeline to start STT streaming
    for the given language.

    Args:
        language_code: BCP-47 language code (e.g. "hi-IN", "gu-IN", "en-US")

    Returns:
        dict with status and the language configured for transcription
    """
    supported = ["hi-IN", "es-ES", "en-US", "gu-IN"]
    if language_code not in supported:
        return {
            "status": "error",
            "message": f"Unsupported language: {language_code}. Choose from {supported}",
        }

    return {
        "status": "ready",
        "language_code": language_code,
        "message": f"STT session configured for {language_code}. Awaiting audio stream.",
        "sample_rate": 16000,
        "encoding": "LINEAR16",
    }


# Register as an ADK FunctionTool
transcribe_audio_tool = FunctionTool(func=transcribe_audio)
