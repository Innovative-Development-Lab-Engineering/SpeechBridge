"""
FastAPI application entry point.
Mounts WebSocket router, configures CORS, and provides health + info endpoints.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.websocket import router as ws_router
from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Set Google credentials env var if not already set
if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info(f"Starting Speech Translation API | Project: {settings.gcp_project_id}")
    logger.info(f"Supported languages: {settings.supported_languages_list}")
    yield
    logger.info("Shutting down Speech Translation API")


app = FastAPI(
    title="SpeechBridge API",
    description="Real-time multilingual speech-to-text and translation using Google Cloud AI + ADK",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────
app.include_router(ws_router)


@app.get("/health", tags=["infrastructure"])
async def health_check():
    return {
        "status": "ok",
        "service": "speech-translation-api",
        "version": "1.0.0",
    }


@app.get("/info", tags=["infrastructure"])
async def info():
    return {
        "supported_languages": settings.supported_languages_list,
        "default_target_language": settings.default_target_language,
        "gcp_project": settings.gcp_project_id,
        "websocket_endpoint": "/ws/translate",
    }
