"""
Run this first:   python check_setup.py

Checks the two things you configured in backend/.env:
  1. DATABASE_URL  -> can we connect, and is pgvector available?
  2. GEMINI_API_KEY -> can we embed text and generate an answer?
"""
import sys

import psycopg

from app.config import settings
from app.shared import gemini


def check(label: str, fn) -> bool:
    try:
        result = fn()
        print(f"  ✅ {label}{f'  ({result})' if result else ''}")
        return True
    except Exception as e:
        print(f"  ❌ {label}\n     {type(e).__name__}: {e}")
        return False


def db_connects():
    with psycopg.connect(settings.database_url, connect_timeout=10) as conn:
        return conn.execute("SHOW server_version").fetchone()[0].split()[0]


def pgvector_available():
    with psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        return "vector " + conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone()[0]


def embedding_works():
    vector = gemini.embed(["hello world"], task="RETRIEVAL_QUERY")[0]
    if len(vector) != settings.embed_dim:
        raise ValueError(f"got {len(vector)} dims, EMBED_DIM is {settings.embed_dim}")
    return f"{settings.embed_model}, {len(vector)} dims"


def generation_works():
    reply = gemini.generate("Reply with the single word: ready")
    return f"{settings.chat_model} said '{reply[:40]}'"


if __name__ == "__main__":
    print("\nDatabase")
    ok = check("connect to DATABASE_URL", db_connects)
    ok = check("pgvector extension", pgvector_available) and ok
    print("\nGemini")
    ok = check("embedding model", embedding_works) and ok
    ok = check("chat model", generation_works) and ok
    print("\n🎉 All good. Start the app: make run   (or: uvicorn app.main:app --reload --port 8000)\n" if ok
          else "\nFix the ❌ items above (see README → Troubleshooting).\n")
    sys.exit(0 if ok else 1)
