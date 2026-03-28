"""
WebSocket handler — Core real-time orchestration endpoint.

Flow per connection:
  1. Client connects to /ws/translate
  2. Client sends AudioConfig JSON message
  3. Client streams binary PCM audio chunks
  4. Backend feeds audio → SpeechService (STT streaming)
  5. On interim transcript → push TranscriptEvent to client
  6. On final transcript → TranslationService.translate() → push TranslationEvent
  7. (Bonus) On final → TTS skill → push TTSAudioEvent
  8. On disconnect → clean shutdown of STT stream
"""

import asyncio
import json
import os
import re
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google.genai import Client, types

from app.config.settings import get_settings
from app.models.schemas import (
    AudioConfig,
    TranscriptEvent,
    TranslationEvent,
    ErrorEvent,
    StatusEvent,
)
from app.services.speech_service import SpeechService
from app.services.translation_service import TranslationService
from app.agent.agent import translation_agent
from app.agent.skills.tts_skill import synthesize_speech
from app.models.schemas import TTSAudioEvent
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


@router.websocket("/ws/translate")
async def translate_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time multilingual translation.

    Protocol:
      - First message (text): AudioConfig JSON
      - Subsequent messages (binary): raw PCM audio chunks at 16kHz LINEAR16
      - Server sends: TranscriptEvent, TranslationEvent, ErrorEvent, StatusEvent
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    speech_service = SpeechService()
    translation_service = TranslationService()

    audio_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    stop_event = asyncio.Event()
    config: AudioConfig = None
    enable_tts = False  # can be enabled via config in future iterations
    transcript_history_buffer = []  # Store last 10 final transcripts for context
    
    # State for throttling interim translations to avoid rate limits
    throttler = {"text": "", "time": 0}

    # Send connected status
    await websocket.send_text(
        StatusEvent(state="connected", message="Ready to receive configuration").model_dump_json()
    )

    async def on_transcript(text: str, is_final: bool, confidence: float, language: str):
        """Callback invoked by SpeechService for each STT result."""
        try:
            # Always push transcript (interim + final)
            transcript_event = TranscriptEvent(
                text=text,
                is_final=is_final,
                language=language,
                confidence=confidence,
            )
            await websocket.send_text(transcript_event.model_dump_json())

            # Translate even interim results to provide a live "on-the-go" experience
            if text.strip():
                target_lang = config.target_language if config else settings.default_target_language
                
                # Build context from the last 15 words of transcript history
                context_words = []
                for entry in transcript_history_buffer[-3:]:  # Last 3 final segments
                    context_words.extend(entry.split())
                
                context_str = " ".join(context_words[-15:]) # Keep last 15 words
                
                # Skip translation when detected source language matches target language
                source_base = language.split("-")[0].lower()
                if source_base == target_lang.lower():
                    translated = text
                    if translated:
                        translation_event = TranslationEvent(
                            original=text,
                            translated=translated,
                            source_language=language,
                            target_language=target_lang,
                            is_final=is_final,
                        )
                        await websocket.send_text(translation_event.model_dump_json())
                        if is_final:
                            transcript_history_buffer.append(text)
                            if len(transcript_history_buffer) > 10:
                                transcript_history_buffer.pop(0)
                    return

                # Use high-fidelity Agent for final translations to support the "uncertainty fallback" rule
                if is_final:
                    try:
                        LANG_NAMES = {
                            "en": "English", "hi": "Hindi",
                            "es": "Spanish", "gu": "Gujarati",
                        }
                        src_name = LANG_NAMES.get(source_base, language)
                        tgt_name = LANG_NAMES.get(target_lang.lower(), target_lang)
                        prompt = f"Translate the following text from {src_name} to {tgt_name}. Output only the translated text, nothing else. Previous context: {context_str}. Text to translate: {text}"
                        
                        # Fix AttributeError: use GenAI client directly for discrete translation tasks
                        client = Client(
                            api_key=settings.google_api_key,
                            vertexai=settings.google_genai_use_vertexai,
                            project=settings.gcp_project_id,
                            location="us-central1"
                        )
                        
                        response = await client.models.generate_content(
                            model=translation_agent.model,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=translation_agent.instruction,
                                temperature=0.3
                            )
                        )
                        translated = response.text
                        
                        # Clear interim state on final
                        throttler["text"] = ""
                        throttler["time"] = 0
                        
                    except Exception as e:
                        logger.error(f"Agent translation failed: {e}. Falling back to standard service.")
                        translated = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: translation_service.translate(
                                text=text,
                                source_lang=language,
                                target_lang=target_lang,
                                context=context_str,
                            ),
                        )
                else:
                    now = time.time()
                    
                    # THROTTE INTERIM: Only translate if significant more text OR > 1.2s passed
                    # This dramatically reduces API calls and avoids rate limits
                    significant_change = len(text) - len(throttler["text"]) > 15
                    enough_time = now - throttler["time"] > 1.2
                    
                    if not (significant_change or enough_time):
                        return # Skip this interim translate cycle
                    
                    throttler["text"] = text
                    throttler["time"] = now
                    
                    # Fast service for on-the-go interim updates
                    translated = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: translation_service.translate(
                            text=text,
                            source_lang=language,
                            target_lang=target_lang,
                            context=context_str,
                        ),
                    )

                if translated:
                    # Clean up any potential agent markers (like "Translation: ")
                    translated = re.sub(r"^(Translation|Result):\s*", "", translated, flags=re.I)
                    
                    translation_event = TranslationEvent(
                        original=text,
                        translated=translated,
                        source_language=language,
                        target_language=target_lang,
                        is_final=is_final,
                    )
                    await websocket.send_text(translation_event.model_dump_json())
                    
                    if is_final:
                        transcript_history_buffer.append(text)
                        if len(transcript_history_buffer) > 10:
                            transcript_history_buffer.pop(0)

                    # Bonus: TTS playback (only for final results as speech takes time)
                    if is_final and enable_tts:
                        tts_result = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: synthesize_speech(translated, target_lang),
                        )
                        if tts_result.get("status") == "success":
                            tts_event = TTSAudioEvent(
                                audio_base64=tts_result["audio_base64"],
                                format="mp3",
                            )
                            await websocket.send_text(tts_event.model_dump_json())

        except Exception as e:
            logger.error(f"Error in transcript callback: {e}")
            try:
                await websocket.send_text(
                    ErrorEvent(message=str(e)).model_dump_json()
                )
            except Exception:
                pass

    try:
        # ── Step 1: Receive AudioConfig ───────────────────────────────────
        raw_config = await websocket.receive_text()
        config_data = json.loads(raw_config)
        config = AudioConfig(**config_data)

        logger.info(f"Session configured: language={config.language_code}, auto_detect={config.auto_detect}")

        await websocket.send_text(
            StatusEvent(
                state="listening",
                message=f"Listening in {config.language_code}",
            ).model_dump_json()
        )

        # ── Step 2: Start STT streaming task ─────────────────────────────
        stt_task = asyncio.create_task(
            speech_service.stream_transcribe(
                audio_queue=audio_queue,
                language_code=config.language_code,
                on_transcript=on_transcript,
                stop_event=stop_event,
            )
        )

        # ── Step 3: Receive audio chunks and enqueue them ─────────────────
        while True:
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
                # Binary audio chunk → enqueue for STT
                try:
                    audio_queue.put_nowait(message["bytes"])
                except asyncio.QueueFull:
                    logger.warning("Audio queue full — dropping chunk")

            elif "text" in message and message["text"]:
                # Handle control messages (e.g., { "type": "stop" })
                try:
                    control = json.loads(message["text"])
                    if control.get("type") == "stop":
                        logger.info("Stop signal received from client")
                        break
                    elif control.get("type") == "enable_tts":
                        enable_tts = True
                        logger.info("TTS enabled for this session")
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        logger.info("Client disconnected")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(ErrorEvent(message=str(e)).model_dump_json())
        except Exception:
            pass

    finally:
        # Clean shutdown
        stop_event.set()
        audio_queue.put_nowait(None)  # Unblock STT generator

        if "stt_task" in dir() and not stt_task.done():
            await asyncio.wait_for(stt_task, timeout=3.0)

        await websocket.send_text(
            StatusEvent(state="disconnected", message="Session ended").model_dump_json()
        )
        logger.info("WebSocket session cleaned up")
