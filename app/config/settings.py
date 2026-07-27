"""Application settings loaded from environment variables and .env."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Global application configuration.
    Values are automatically loaded from .env.
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ==========================
    # Application
    # ==========================
    app_name: str = "Olympiad AI Video Generator"
    app_env: str = "development"

    host: str = "0.0.0.0"
    port: int = 8000

    # ==========================
    # Logging
    # ==========================
    log_level: str = "INFO"

    # ==========================
    # AI Providers
    # ==========================
    google_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_embedding_model: str = "mxbai-embed-large:latest"
    ollama_embedding_timeout_seconds: float = 3600.0
    ollama_request_timeout_seconds: float = 3600.0
    ollama_connect_timeout_seconds: float = 15.0
    ollama_max_retries: int = 2
    ollama_retry_backoff_seconds: float = 2.0
    ollama_num_predict: int = 4096
    ollama_context_window: int = 8192
    ollama_keep_alive: str = "10m"
    llm_content_char_limit: int = 8000
    llm_source_context_char_limit: int = 6000
    max_local_retries_before_escalation: int = 2

    default_provider: str = "gemini"
    default_model: str = "gemini-2.5-pro"

    # ==========================
    # Directories
    # ==========================
    upload_directory: str = str(PROJECT_ROOT / "uploads")
    output_directory: str = str(PROJECT_ROOT / "output_new")
    prompts_directory: str = str(PROJECT_ROOT / "prompts")

    # ==========================
    # Rendering
    # ==========================
    ffmpeg_path: str = "ffmpeg"
    tts_model: str = "tts-1"
    tts_voice: str = "alloy"
    redis_url: str = "redis://localhost:6379/0"

    @model_validator(mode="after")
    def resolve_paths(self) -> "Settings":
        for field in ["upload_directory", "output_directory", "prompts_directory"]:
            val = getattr(self, field)
            path = Path(val)
            if not path.is_absolute():
                setattr(self, field, str(PROJECT_ROOT / path))
        return self


@lru_cache
def get_settings() -> Settings:
    """
    Returns a singleton Settings instance.
    """
    return Settings()
