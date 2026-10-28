"""
Postgres + pgvector: connection and table setup.

Two tables hold everything:
    documents  -> one row per uploaded file (status, steps log)
    chunks     -> one row per searchable piece of text, with
                  * embedding  : vector for meaning-based search
                  * tsv        : keyword index for exact-word search (auto-filled by Postgres)
"""
from contextlib import contextmanager

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


def init_schema() -> None:
    """Create the extension, tables and indexes if they don't exist yet. Safe to run on every start."""
    lang = settings.text_search_language
    dim = settings.embed_dim
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                filename      TEXT NOT NULL,
                content_hash  TEXT NOT NULL UNIQUE,
                status        TEXT NOT NULL DEFAULT 'queued',   -- queued | processing | ready | failed
                error         TEXT,
                num_chunks    INT NOT NULL DEFAULT 0,
                steps         JSONB NOT NULL DEFAULT '[]',      -- ingestion trace shown in the UI
                created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS chunks (
                id           BIGSERIAL PRIMARY KEY,
                document_id  UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index  INT NOT NULL,
                page         INT,
                content      TEXT NOT NULL,
                embedding    vector({dim}) NOT NULL,
                tsv          tsvector GENERATED ALWAYS AS (to_tsvector('{lang}', content)) STORED
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops)")
        conn.execute("CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin (tsv)")
        conn.execute("CREATE INDEX IF NOT EXISTS chunks_document_idx ON chunks (document_id)")

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
