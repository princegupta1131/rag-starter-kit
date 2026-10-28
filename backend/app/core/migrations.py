"""
Runs backend/sql/migrations/*.sql in order, once each, on startup.

Applied versions are recorded in the schema_migrations table.
Add a change: create the next numbered file (e.g. 003_add_tags.sql). Never edit an applied one.

The files are plain SQL, so you can also run them by hand with psql.
They are written with the defaults EMBED_DIM=768 and TEXT_SEARCH_LANGUAGE=english;
other values are substituted here.
"""
import logging

import psycopg

from app.config import BACKEND_DIR, settings

MIGRATIONS_DIR = BACKEND_DIR / "sql" / "migrations"
LOCK_ID = 7_150_031  # any constant: stops two servers migrating at the same time
log = logging.getLogger(__name__)


def run_migrations() -> list[str]:
    applied: list[str] = []
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        conn.execute("SELECT pg_advisory_lock(%s)", (LOCK_ID,))
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
            done = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
            for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
                if path.stem in done:
                    continue
                with conn.transaction():
                    conn.execute(_render(path.read_text(encoding="utf-8")))
                    conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
                applied.append(path.stem)
                log.info("applied migration %s", path.stem)
            _check_embedding_dim(conn)
        finally:
            conn.execute("SELECT pg_advisory_unlock(%s)", (LOCK_ID,))
    return applied


def _render(sql: str) -> str:
    return sql.replace("vector(768)", f"vector({settings.embed_dim})").replace(
        "to_tsvector('english'", f"to_tsvector('{settings.text_search_language}'"
    )


def _check_embedding_dim(conn: psycopg.Connection) -> None:
    """The vector size is fixed when the table is created; catch a changed EMBED_DIM early."""
    row = conn.execute(
        "SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
        "WHERE attrelid = 'chunks'::regclass AND attname = 'embedding'"
    ).fetchone()
    if row and row[0] != f"vector({settings.embed_dim})":
        raise RuntimeError(
            f"chunks.embedding is {row[0]} but EMBED_DIM={settings.embed_dim}. "
            "Set EMBED_DIM back, or start with an empty database."
        )
