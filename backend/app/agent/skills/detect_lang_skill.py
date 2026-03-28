"""
Detect Language Skill — ADK Tool for language detection.
Uses Google Translate API to detect the language of transcribed text.
"""

from google.adk.tools import FunctionTool
from app.services.translation_service import TranslationService

_translation_service = TranslationService()

LANGUAGE_NAMES = {
    "hi": "Hindi",
    "gu": "Gujarati",
    "es": "Spanish",
    "en": "English",
    "mr": "Marathi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "pa": "Punjabi",
    "ur": "Urdu",
}


def detect_language(text: str) -> dict:
    """
    ADK Skill: Detect the language of the given text.

    Useful when auto_detect mode is enabled and the user hasn't
    manually selected a language before speaking.

    Args:
        text: Text to detect language from (usually first STT result)

    Returns:
        dict with detected language code, human-readable name, and confidence
    """
    if not text or not text.strip():
        return {"status": "error", "message": "No text to detect language from"}

    result = _translation_service.detect_language(text)
    lang_code = result.get("language", "und")
    confidence = result.get("confidence", 0.0)
    lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())

    return {
        "status": "success",
        "detected_language": lang_code,
        "language_name": lang_name,
        "bcp47_code": f"{lang_code}-IN" if lang_code in ("hi", "gu", "mr") else f"{lang_code}-ES" if lang_code == "es" else lang_code,
        "confidence": round(confidence, 4),
        "reliable": confidence > 0.7,
    }


detect_language_tool = FunctionTool(func=detect_language)
