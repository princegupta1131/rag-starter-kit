"""
Postgres connection pool. Every query in the app goes through get_conn().

    with get_conn() as conn:
        conn.execute("SELECT 1")

The pool opens on startup (main.py) and lazily in scripts/tests.
On startup the database itself is created if it doesn't exist (ensure_database),
then the tables by core/migrations.py from backend/sql/migrations/.
"""
from contextlib import contextmanager

import psycopg
from pgvector.psycopg import register_vector
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg_pool import ConnectionPool

from app.config import settings

_pool: ConnectionPool | None = None

# Common connection errors -> what to do about them
_HINTS = [
    ("password authentication failed", "Wrong user or password in DATABASE_URL."),
    ('role "', "That user doesn't exist on this server. Fix the user in DATABASE_URL."),
    ("Connection refused", "Postgres isn't running, or the host/port in DATABASE_URL is wrong."),
    ("could not translate host name", "The host in DATABASE_URL is wrong."),
    ("timeout expired", "Can't reach the database server. Check the host and your network."),
    ('"vector" is not available', "This Postgres has no pgvector. Install it, or use Supabase / Neon."),
    ("permission denied to create", "Your database user can't do this. Create it as an admin, or ask for access."),
]


def ensure_database() -> bool:
    """Creates the database named in DATABASE_URL if it doesn't exist yet. Returns True if it was created."""
    name = conninfo_to_dict(settings.database_url).get("dbname")
    try:
        psycopg.connect(settings.database_url, connect_timeout=10).close()
        return False
    except psycopg.OperationalError as e:
        if not name or f'database "{name}" does not exist' not in str(e):
            raise
    admin_url = make_conninfo(settings.database_url, dbname="postgres")
    with psycopg.connect(admin_url, autocommit=True, connect_timeout=10) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    return True


def explain_db_error(e: Exception) -> str:
    """One readable line instead of libpq's multi-line message."""
    text = str(e)
    # libpq: 'connection failed: connection to server at "...", port 5432 failed: FATAL:  <reason>'
    reason = text.split("FATAL:")[-1].split(" failed: ")[-1].strip().splitlines()[0].rstrip(".") if text else ""
    reason = reason or type(e).__name__
    hint = next((h for needle, h in _HINTS if needle in text), "")
    return f"{reason}. {hint}".strip()


def open_pool() -> None:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            settings.database_url,
            min_size=1,
            max_size=settings.db_pool_max,
            kwargs={"autocommit": True},
            configure=register_vector,  # lets psycopg send/receive pgvector values
            open=True,
        )


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def get_conn():
    if _pool is None:
        open_pool()
    with _pool.connection() as conn:
        yield conn
