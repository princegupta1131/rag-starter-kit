"""
Every setting the app uses, read from backend/.env.

Only TWO values are required:
    DATABASE_URL    -> your Postgres (with the pgvector extension)
    GEMINI_API_KEY  -> your Google AI Studio key

Everything else has a sensible default you can tune during the hands-on.
"""
import re
import sys
from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    # --- Required -------------------------------------------------------
    database_url: str
    gemini_api_key: str

    # --- Models ---------------------------------------------------------
    chat_model: str = "gemini-3.5-flash-lite"   # writes answers + rewrites queries
    vision_model: str = "gemini-3.5-flash-lite"  # describes uploaded images
    embed_model: str = "gemini-embedding-001"   # turns text into vectors
    embed_dim: int = 768                         # vector size stored in Postgres

    # --- Ingestion ------------------------------------------------------
    chunk_size_words: int = 200      # target words per chunk
    chunk_overlap_words: int = 40    # words repeated between neighbouring chunks
    max_upload_mb: int = 20

    # --- Retrieval ------------------------------------------------------
    top_k: int = 6                   # chunks sent to the LLM
    candidates_per_search: int = 20  # chunks each search (vector / keyword) returns before fusion
    min_similarity: float = 0.50     # evidence gate: below this we say "not found"
    query_rewrite: bool = True       # LLM cleans up / completes the question before search
    strict_citations: bool = True    # refuse answers that cite no source
    cache_ttl_seconds: int = 600
    text_search_language: str = "english"  # Postgres full-text config ("simple" for mixed languages)

    # --- Server ---------------------------------------------------------
    cors_origins: str = "http://localhost:5173"

    @field_validator("database_url")
    @classmethod
    def _plain_postgres_url(cls, v: str) -> str:
        # Accept SQLAlchemy-style URLs people often copy from other projects.
        return v.replace("postgresql+psycopg://", "postgresql://").replace("postgres+psycopg://", "postgresql://")

    @field_validator("text_search_language")
    @classmethod
    def _safe_identifier(cls, v: str) -> str:
        if not re.fullmatch(r"[a-z_]+", v):
            raise ValueError("must be a Postgres text search config name, e.g. english or simple")
        return v


@lru_cache
def get_settings() -> Settings:
    try:
        loaded = Settings()
    except ValidationError as e:
        missing = [str(err["loc"][0]).upper() for err in e.errors() if err["type"] == "missing"]
        if missing:
            sys.exit(
                f"\n❌ Missing {', '.join(missing)}.\n"
                f"   Copy backend/.env.example to backend/.env and fill it in.\n"
            )
        raise
    if loaded.gemini_api_key.strip() in ("", "your-gemini-api-key"):
        sys.exit(
            "\n❌ GEMINI_API_KEY is still the placeholder.\n"
            "   Put your key in backend/.env (get one at https://aistudio.google.com/apikey).\n"
        )
    return loaded


settings = get_settings()
