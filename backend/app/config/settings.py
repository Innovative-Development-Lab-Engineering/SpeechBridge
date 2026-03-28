from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Google Cloud
    google_application_credentials: str = "../stt.json"
    gcp_project_id: str = "nyuhackathon"

    # Translation defaults
    default_target_language: str = "en"
    supported_languages: str = "en-US,hi-IN,es-ES,gu-IN"

    # ADK / Gemini
    google_api_key: str = ""
    google_genai_use_vertexai: bool = False

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Audio
    audio_sample_rate: int = 16000
    audio_chunk_size: int = 1600

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def supported_languages_list(self) -> List[str]:
        return [l.strip() for l in self.supported_languages.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
