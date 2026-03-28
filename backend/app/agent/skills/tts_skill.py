"""
TTS Skill — ADK Tool wrapping Google Cloud Text-to-Speech API.
BONUS: Synthesizes translated English text into audio for playback.
"""

import base64
from google.adk.tools import FunctionTool
from google.cloud import texttospeech
from app.utils.logger import get_logger

logger = get_logger(__name__)

VOICE_MAP = {
    "en": texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        name="en-US-Neural2-C",
    ),
    "hi": texttospeech.VoiceSelectionParams(
        language_code="hi-IN",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    ),
    "es": texttospeech.VoiceSelectionParams(
        language_code="es-ES",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    ),
}


def synthesize_speech(text: str, language: str = "en") -> dict:
    """
    ADK Skill: Convert text to speech and return base64-encoded MP3 audio.

    Args:
        text:     Text to synthesize (typically the translated English output)
        language: ISO 639-1 language code (default: "en" for English)

    Returns:
        dict with base64-encoded audio and format metadata
    """
    if not text or not text.strip():
        return {"status": "error", "message": "No text to synthesize"}

    try:
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = VOICE_MAP.get(language, VOICE_MAP["en"])
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0,
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
        logger.info(f"TTS synthesized {len(text)} chars in language '{language}'")

        return {
            "status": "success",
            "audio_base64": audio_b64,
            "format": "mp3",
            "language": language,
            "text": text,
        }

    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        return {"status": "error", "message": str(e)}


synthesize_speech_tool = FunctionTool(func=synthesize_speech)
