"""
Checks your backend/.env before you start:  make check   (or: python check_setup.py)

  1. DATABASE_URL  -> can we connect (creating the database if needed), and is pgvector available?
  2. LLM provider  -> can we embed text and generate an answer?
"""
import sys

import psycopg

from app.config import settings
from app.core.database import ensure_database, explain_db_error
from app.providers import get_chat_model, get_embedder


def check(label: str, fn) -> bool:
    try:
        result = fn()
        print(f"  ✅ {label}{f'  ({result})' if result else ''}")
        return True
    except psycopg.Error as e:
        print(f"  ❌ {label}\n     {explain_db_error(e)}")
    except Exception as e:
        print(f"  ❌ {label}\n     {str(e).strip().splitlines()[0][:300]}")
    return False


def db_connects():
    created = ensure_database()
    with psycopg.connect(settings.database_url, connect_timeout=10) as conn:
        version = "Postgres " + conn.execute("SHOW server_version").fetchone()[0].split()[0]
    return f"{version}, database created" if created else version


def pgvector_available():
    with psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        return "vector " + conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone()[0]


def embedding_works():
    vector = get_embedder().embed_query("hello world")
    if len(vector) != settings.embed_dim:
        raise ValueError(f"got {len(vector)} dims, EMBED_DIM is {settings.embed_dim}")
    return f"{settings.embed_model}, {len(vector)} dims"


def generation_works():
    reply = get_chat_model().generate("Reply with the single word: ready")
    return f"{settings.chat_model} said '{reply[:40]}'"


if __name__ == "__main__":
    print("\nDatabase")
    db_ok = check("connect to DATABASE_URL", db_connects)
    db_ok = db_ok and check("pgvector extension", pgvector_available)
    print(f"\nLLM provider: {settings.llm_provider}")
    llm_ok = check("embedding model", embedding_works)
    llm_ok = check("chat model", generation_works) and llm_ok
    ok = db_ok and llm_ok
    print("\n🎉 All good. Start the app: make run\n" if ok else "\nFix the ❌ items above (see docs/SETUP_GUIDE.md).\n")
    sys.exit(0 if ok else 1)
