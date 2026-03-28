"""
Root ADK Agent — Speech Translation Agent.

Orchestrates the four skills:
  1. transcribe_audio  — Configure STT for selected language
  2. detect_language   — Auto-detect language from text (optional)
  3. translate_text    — Translate transcript to English
  4. synthesize_speech — Convert translated text to audio (bonus TTS)

The agent is invoked by the WebSocket handler for tool-based processing.
For the raw audio streaming path, the services are used directly.
"""

from google.adk.agents import Agent

from app.agent.skills.transcribe_skill import transcribe_audio
from app.agent.skills.translate_skill import translate_text
from app.agent.skills.detect_lang_skill import detect_language
from app.agent.skills.tts_skill import synthesize_speech
from app.config.settings import get_settings

settings = get_settings()

# ─── Agent Definition ────────────────────────────────────────────────────────

translation_agent = Agent(
    name="speech_translation_agent",
    model="gemini-1.5-flash",
    description=(
        "A real-time multilingual speech transcription and translation agent. "
        "Supports Hindi, Spanish, Gujarati, and English. Translates all input pairs."
    ),
    instruction="""
You are a real-time speech translation assistant. Your goal is high-accuracy translation between Hindi, Spanish, Gujarati, and English.

RULES:
1. Translate the input accurately to the requested target language.
2. HYBRID TRANSLATION: If you are unsure about a specific word, or if the best equivalent is the English term, keep that specific word as it is (in English) within the translated sentence.
3. Be natural and conversational.
4. Support all directions (e.g. Gujarati to Spanish, Hindi to English, etc.).
""",
    tools=[transcribe_audio, detect_language, translate_text, synthesize_speech],
)
