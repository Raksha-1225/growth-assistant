
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    app_env: str = "dev"
    log_level: str = "INFO"

    database_url: str = (
        "postgresql+asyncpg://lenny:lenny@db:5432/lenny"
    )

    llm_provider: str = "ollama"
    fallback_provider: str = ""
    llm_timeout_seconds: int = 120

    ollama_base_url: str = (
        "http://host.docker.internal:11434"
    )
    ollama_chat_model: str = "qwen2.5-coder:3b"
    ollama_embed_model: str = "nomic-embed-text"

    cloud_api_key: str = ""
    cloud_base_url: str = (
        "https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    cloud_model: str = "gemini-2.0-flash"
    transcripts_dir: str = "/data/transcripts/episodes"
    retrieval_top_k: int = 4
    retrieval_min_score: float = 0.45

@lru_cache
def get_settings() -> Settings:
    return Settings()
