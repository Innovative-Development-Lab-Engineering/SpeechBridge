"""
Speech Service — Google Cloud Speech-to-Text streaming wrapper.

Promoted and refactored from the original live_transcribe.py.
Accepts audio bytes from WebSocket (not PyAudio directly) so it works
both in the web server and in standalone CLI mode.
"""

import asyncio
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator, Callable, Optional

from google.cloud import speech

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Matches the original live_transcribe.py constants
RATE = settings.audio_sample_rate
CHUNK = settings.audio_chunk_size

# Google STT has a 5-minute streaming limit; reset before that
STREAMING_LIMIT = 240  # seconds


class SpeechService:
    """
    Manages a Google Cloud STT streaming session.
    Accepts raw PCM audio bytes from any source (WebSocket, PyAudio, file)
    and yields transcript results via an async callback.
    """

    def __init__(self):
        self._client = speech.SpeechClient()
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _build_config(self, language_code: str) -> speech.StreamingRecognitionConfig:
        """Build the STT streaming config for a given language."""
        recognition_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code=language_code,
            alternative_language_codes=self._get_alternative_codes(language_code),
            enable_automatic_punctuation=True,
            use_enhanced=True,
            model="latest_long",
        )
        return speech.StreamingRecognitionConfig(
            config=recognition_config,
            interim_results=True,
            single_utterance=False, # Wait for user to stop or limit
        )

    def _get_alternative_codes(self, primary: str) -> list[str]:
        """Return fallback language codes (helps with code-switching)."""
        all_codes = settings.supported_languages_list
        return [code for code in all_codes if code != primary]

    async def stream_transcribe(
        self,
        audio_queue: asyncio.Queue,
        language_code: str,
        on_transcript: Callable,
        stop_event: asyncio.Event,
    ) -> None:
        """
        Core streaming method. Reads from audio_queue, sends to Google STT,
        calls on_transcript(text, is_final, confidence, language) for each result.

        Runs the blocking gRPC call in a ThreadPoolExecutor to avoid
        blocking the FastAPI async event loop.

        Args:
            audio_queue:   asyncio.Queue of raw PCM bytes from WebSocket
            language_code: BCP-47 language code e.g. "hi-IN"
            on_transcript: async callable(text, is_final, confidence, language)
            stop_event:    signal to cleanly stop the session
        """
        loop = asyncio.get_event_loop()
        sync_queue: queue.Queue = queue.Queue()

        # Bridge: move bytes from async queue → sync queue for gRPC thread
        async def _drain_to_sync():
            while not stop_event.is_set():
                try:
                    chunk = await asyncio.wait_for(audio_queue.get(), timeout=0.1)
                    sync_queue.put(chunk)
                except asyncio.TimeoutError:
                    continue
            sync_queue.put(None)  # sentinel to stop generator

        def _audio_generator():
            """Sync generator consumed by the STT client."""
            while True:
                chunk = sync_queue.get()
                if chunk is None:
                    return
                yield speech.StreamingRecognizeRequest(audio_content=chunk)

        def _run_stt():
            """Blocking STT call — runs in thread pool with infinite reconnect loop."""
            while not stop_event.is_set():
                config = self._build_config(language_code)
                logger.info(f"Starting/Restarting STT stream for {language_code}...")
                try:
                    responses = self._client.streaming_recognize(
                        config=config,
                        requests=_audio_generator(),
                    )
                    for response in responses:
                        if stop_event.is_set():
                            break
                        if not response.results:
                            continue
                        result = response.results[0]
                        if not result.alternatives:
                            continue

                        text = result.alternatives[0].transcript
                        confidence = (
                            result.alternatives[0].confidence
                            if result.is_final
                            else None
                        )
                        detected_lang = language_code
                        if hasattr(result, "language_code") and result.language_code:
                            detected_lang = result.language_code

                        asyncio.run_coroutine_threadsafe(
                            on_transcript(text, result.is_final, confidence, detected_lang),
                            loop,
                        )
                except Exception as e:
                    if stop_event.is_set():
                        break
                    logger.warning(f"STT stream reset: {e}")
                    # Brief sleep to avoid rapid retries on hard errors
                    import time
                    time.sleep(1)

        # Run drain and STT concurrently
        drain_task = asyncio.create_task(_drain_to_sync())
        await loop.run_in_executor(self._executor, _run_stt)
        await drain_task

        logger.info(f"STT session ended for language: {language_code}")
