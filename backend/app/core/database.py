"""
Postgres connection pool. Every query in the app goes through get_conn().

    with get_conn() as conn:
        conn.execute("SELECT 1")

The pool opens on startup (main.py) and lazily in scripts/tests.
Tables are created by core/migrations.py from backend/sql/migrations/.
"""
from contextlib import contextmanager

from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

from app.config import settings

_pool: ConnectionPool | None = None


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
