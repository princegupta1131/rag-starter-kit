"""SQL for the collections table."""
from uuid import UUID

import psycopg

from app.core.database import get_conn

_COLUMNS = """
    c.id, c.name, c.description, c.created_at,
    count(d.id) AS document_count,
    count(d.id) FILTER (WHERE d.status = 'ready') AS ready_count
"""


def list_all() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT {_COLUMNS} FROM collections c LEFT JOIN documents d ON d.collection_id = c.id "
            "GROUP BY c.id ORDER BY c.created_at"
        ).fetchall()
    return [_row(r) for r in rows]


def get(collection_id: UUID) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT {_COLUMNS} FROM collections c LEFT JOIN documents d ON d.collection_id = c.id "
            "WHERE c.id = %s GROUP BY c.id",
            (collection_id,),
        ).fetchone()
    return _row(row) if row else None


def create(name: str, description: str) -> dict | None:
    """Returns None if the name is already taken."""
    try:
        with get_conn() as conn:
            (new_id,) = conn.execute(
                "INSERT INTO collections (name, description) VALUES (%s, %s) RETURNING id", (name, description)
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        return None
    return get(new_id)


def delete(collection_id: UUID) -> bool:
    """Deletes the collection and (by cascade) its documents and chunks."""
    with get_conn() as conn:
        row = conn.execute("DELETE FROM collections WHERE id = %s RETURNING id", (collection_id,)).fetchone()
    return row is not None


def _row(r) -> dict:
    keys = ("id", "name", "description", "created_at", "document_count", "ready_count")
    return dict(zip(keys, r, strict=True))
