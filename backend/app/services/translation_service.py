"""
Translation Service — Google Cloud Translation API v2 wrapper.
Handles text translation with retry logic and language skip optimization.
"""

import time
import html
from typing import Optional

from google.cloud import translate_v2 as translate

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Language codes that map to English — skip translation for these
ENGLISH_CODES = {"en", "en-US", "en-GB", "en-AU", "en-IN"}

# Retry config
MAX_RETRIES = 3
RETRY_BASE_DELAY = 0.5  # seconds, doubles each retry


class TranslationService:
    """
    Wraps the Google Cloud Translation API v2.
    Provides synchronous translation with retry and deduplication.
    """

    def __init__(self):
        self._client = translate.Client()
        self._cache: dict[str, str] = {}  # simple in-memory cache

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str = "en",
        context: str = "",
    ) -> Optional[str]:
        """
        Translate `text` from `source_lang` to `target_lang`.

        Returns None if:
        - text is empty
        - source and target are both English variants
        - API call fails after retries

        Args:
            text:        Text to translate
            source_lang: BCP-47 source language code (e.g. "hi-IN")
            target_lang: ISO 639-1 target language code (default: "en")
        """
        if not text or not text.strip():
            return None

        # Normalize source language to base code (hi-IN → hi)
        source_base = source_lang.split("-")[0].lower()
        target_base = target_lang.split("-")[0].lower()

<<<<<<< HEAD
        # Skip if already in target language
        if source_base == target_base:
=======
        # Skip if source and target are the same language
        if source_base == target_lang.lower():
>>>>>>> abc7bf02ec75f2255b2116d129630446cac728d6
            logger.debug(f"Skipping translation — source ({source_lang}) == target ({target_lang})")
            return text

        # Check simple cache
        cache_key = f"{source_lang}:{target_lang}:{text}"
        if cache_key in self._cache:
            logger.debug("Translation cache hit")
            return self._cache[cache_key]

        # Prepend context to improve translation nuances (pronouns, gender, etc.)
        # We use a unique separator to reliably extract the new translation
        separator = " || "
        query_text = f"{context}{separator}{text}" if context else text

        # Attempt translation with retries
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = self._client.translate(
                    query_text,
                    source_language=source_base,
                    target_language=target_lang,
                    format_="text",
                )
                raw_translated = html.unescape(result["translatedText"])
                
                # Extract only the newly translated part
                if separator in raw_translated:
                    translated = raw_translated.split(separator)[-1].strip()
                else:
                    translated = raw_translated

                # Store in cache (bounded to 512 entries to avoid memory leak)
                if len(self._cache) < 512:
                    self._cache[cache_key] = translated

                logger.info(
                    f"Translated [{source_lang}→{target_lang}]: "
                    f'"{text[:40]}..." → "{translated[:40]}..."'
                )
                return translated

            except Exception as e:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    f"Translation attempt {attempt}/{MAX_RETRIES} failed: {e}. "
                    f"Retrying in {delay}s..."
                )
                if attempt < MAX_RETRIES:
                    time.sleep(delay)
                else:
                    logger.error(f"Translation failed after {MAX_RETRIES} attempts: {e}")
                    return None

    def detect_language(self, text: str) -> dict:
        """
        Detect the language of the given text.
        Returns: { "language": "hi", "confidence": 0.99 }
        """
        try:
            result = self._client.detect_language(text)
            return {
                "language": result.get("language", "und"),
                "confidence": result.get("confidence", 0.0),
            }
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {"language": "und", "confidence": 0.0}
