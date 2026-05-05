from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL — set DATABASE_URL directly, or use individual fields
    database_url: Optional[str] = None   # e.g. postgresql://user:pass@host:5432/dbname
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "fallout_db"
    db_user: str = "postgres"
    db_password: str = ""

    # DB schema for fallout metadata table
    db_schema: str = "bosssvc"

    # LLM provider: "anthropic" | "groq" | "gemini" | "ollama"
    llm_provider: str = "groq"
    llm_max_tokens: int = 1024

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Groq  (free tier – get key at console.groq.com)
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"

    # Google Gemini  (free tier – get key at aistudio.google.com)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # Ollama  (fully local – no API key needed)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Meta matching: score >= this threshold returns resolution directly without LLM
    meta_confidence_threshold: int = 5

    # App
    app_title: str = "AI Fallout Manager"
    app_version: str = "1.0.0"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def async_db_dsn(self) -> str:
        if self.database_url:
            return self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            ).replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
