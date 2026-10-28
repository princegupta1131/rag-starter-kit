"""
Postgres + pgvector: connection and table setup.

The tables are defined in backend/sql/schema.sql:
    documents  -> one row per uploaded file (status, steps log)
    chunks     -> one row per searchable piece of text, with
                  * embedding  : vector for meaning-based search
                  * tsv        : keyword index for exact-word search (auto-filled by Postgres)
"""
from contextlib import contextmanager
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

from app.config import settings


@contextmanager
def get_conn():
    """Open a connection, hand it out, always close it."""
    conn = psycopg.connect(settings.database_url, autocommit=True)
    try:
        register_vector(conn)
        yield conn
    finally:
        conn.close()


SCHEMA_FILE = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"


def init_schema() -> None:
    """Run backend/sql/schema.sql. Safe on every start: it only creates what is missing."""
    lang = settings.text_search_language
    dim = settings.embed_dim
    # schema.sql is written with the defaults; swap in this project's settings
    sql = SCHEMA_FILE.read_text(encoding="utf-8")
    sql = sql.replace("vector(768)", f"vector({dim})").replace("to_tsvector('english'", f"to_tsvector('{lang}'")
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        conn.execute(sql)

        # The vector size is fixed when the table is created. Catch a changed EMBED_DIM early.
        row = conn.execute(
            "SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
            "WHERE attrelid = 'chunks'::regclass AND attname = 'embedding'"
        ).fetchone()
        if row and row[0] != f"vector({dim})":
            raise RuntimeError(
                f"chunks.embedding is {row[0]} but EMBED_DIM={dim}. "
                f"Drop the tables (DROP TABLE chunks, documents;) or set EMBED_DIM back."
            )


def recover_interrupted_jobs() -> None:
    """If the server stopped mid-ingestion, mark those documents as failed so they can be re-uploaded."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE documents SET status = 'failed', error = 'Server restarted during ingestion. Delete and upload again.' "
            "WHERE status IN ('queued', 'processing')"
        )
