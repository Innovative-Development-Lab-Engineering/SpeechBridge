"""
Translate Skill — ADK Tool wrapping Google Cloud Translation API.
Used by the translation_agent to translate transcribed text into English.
"""

from google.adk.tools import FunctionTool
from app.services.translation_service import TranslationService

_translation_service = TranslationService()


def translate_text(text: str, source_language: str, target_language: str = "en") -> dict:
    """
    ADK Skill: Translate text from source_language into target_language.

    Args:
        text:            The transcribed text to translate
        source_language: BCP-47 source language code (e.g. "hi-IN")
        target_language: ISO 639-1 target language code (default: "en")

    Returns:
        dict with original text, translated text, and language metadata
    """
    if not text or not text.strip():
        return {"status": "error", "message": "Empty text provided"}

    translated = _translation_service.translate(
        text=text,
        source_lang=source_language,
        target_lang=target_language,
    )

    if translated is None:
        return {
            "status": "error",
            "message": "Translation failed. Please retry.",
            "original": text,
        }

    return {
        "status": "success",
        "original": text,
        "translated": translated,
        "source_language": source_language,
        "target_language": target_language,
    }


translate_text_tool = FunctionTool(func=translate_text)
