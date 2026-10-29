"""
All settings, read from backend/.env (see .env.example for the full list).

Required: DATABASE_URL, plus the API key for your LLM_PROVIDER
(GEMINI_API_KEY by default, or OPENAI_API_KEY with LLM_PROVIDER=openai).
"""
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

PROVIDER_DEFAULTS = {
    "gemini": {"chat_model": "gemini-3.5-flash-lite", "embed_model": "gemini-embedding-001"},
    "openai": {"chat_model": "gpt-6-luna", "embed_model": "text-embedding-3-small"},
}
PLACEHOLDER_KEYS = {"", "your-gemini-api-key", "your-openai-api-key"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    # Required
    database_url: str

    # LLM provider
    llm_provider: Literal["gemini", "openai"] = "gemini"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    chat_model: str = ""   # empty = provider default (PROVIDER_DEFAULTS)
    embed_model: str = ""  # empty = provider default
    embed_dim: int = 768   # fixed once the tables exist

    # Ingestion
    chunk_size_words: int = 200
    chunk_overlap_words: int = 40
    max_upload_mb: int = 20

    # Retrieval
    top_k: int = 6
    candidates_per_search: int = 20
    min_similarity: float = 0.50
    context_margin: float = 0.12   # also drop chunks this far below the best match
    query_rewrite: bool = True
    strict_citations: bool = True
    cache_ttl_seconds: int = 600
    text_search_language: str = "english"

    # Server
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"
    db_pool_max: int = 10

    @field_validator("database_url")
    @classmethod
    def _plain_postgres_url(cls, v: str) -> str:
        return v.replace("postgresql+psycopg://", "postgresql://").replace("postgres+psycopg://", "postgresql://")

    @field_validator("text_search_language")
    @classmethod
    def _safe_identifier(cls, v: str) -> str:
        if not re.fullmatch(r"[a-z_]+", v):
            raise ValueError("must be a Postgres text search config name, e.g. english or simple")
        return v

    @model_validator(mode="after")
    def _provider_defaults(self) -> "Settings":
        defaults = PROVIDER_DEFAULTS[self.llm_provider]
        self.chat_model = self.chat_model or defaults["chat_model"]
        self.embed_model = self.embed_model or defaults["embed_model"]
        return self

    @property
    def api_key(self) -> str:
        return self.gemini_api_key if self.llm_provider == "gemini" else self.openai_api_key

    @property
    def api_key_name(self) -> str:
        return f"{self.llm_provider.upper()}_API_KEY"


@lru_cache
def get_settings() -> Settings:
    try:
        loaded = Settings()
    except ValidationError as e:
        missing = [str(err["loc"][0]).upper() for err in e.errors() if err["type"] == "missing"]
        if missing:
            sys.exit(
                f"\n❌ Missing {', '.join(missing)}.\n"
                "   Copy backend/.env.example to backend/.env and fill it in.\n"
            )
        raise
    problems = []
    if "USER:PASSWORD" in loaded.database_url:
        problems.append("DATABASE_URL still has the example USER:PASSWORD. Put your database user and password.")
    if loaded.api_key.strip() in PLACEHOLDER_KEYS:
        problems.append(f"{loaded.api_key_name} is not set. Put your key (LLM_PROVIDER={loaded.llm_provider}).")
    if problems:
        sys.exit("\n" + "".join(f"❌ {p}\n" for p in problems) + "   Edit backend/.env, then try again.\n")
    return loaded


settings = get_settings()
