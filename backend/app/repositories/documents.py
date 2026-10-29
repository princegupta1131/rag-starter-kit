"""SQL for the documents table."""
from uuid import UUID

from psycopg.types.json import Jsonb

from app.core.database import get_conn

_COLUMNS = "id, collection_id, filename, status, error, num_chunks, embed_model, steps, created_at"


def list_for_collection(collection_id: UUID | None = None) -> list[dict]:
    where, params = ("WHERE collection_id = %s", (collection_id,)) if collection_id else ("", ())
    with get_conn() as conn:
        rows = conn.execute(f"SELECT {_COLUMNS} FROM documents {where} ORDER BY created_at DESC", params).fetchall()
    return [_row(r) for r in rows]


def find_by_hash(collection_id: UUID, content_hash: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT {_COLUMNS} FROM documents WHERE collection_id = %s AND content_hash = %s",
            (collection_id, content_hash),
        ).fetchone()
    return _row(row) if row else None


def create(collection_id: UUID, filename: str, content_hash: str, embed_model: str) -> str | None:
    """Returns None if this collection already has a file with the same content."""
    with get_conn() as conn:
        row = conn.execute(
            "INSERT INTO documents (collection_id, filename, content_hash, embed_model) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (collection_id, content_hash) DO NOTHING RETURNING id",
            (collection_id, filename, content_hash, embed_model),
        ).fetchone()
    return str(row[0]) if row else None


def delete(document_id: UUID | str) -> bool:
    with get_conn() as conn:
        return conn.execute("DELETE FROM documents WHERE id = %s RETURNING id", (document_id,)).fetchone() is not None


def set_status(document_id: str, status: str, steps: list[dict], error: str | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE documents SET status = %s, error = %s, steps = %s WHERE id = %s",
            (status, error, Jsonb(steps), document_id),
        )


def mark_interrupted() -> int:
    """Documents left mid-ingestion by a restart become 'failed' so they can be uploaded again."""
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE documents SET status = 'failed', error = 'Server restarted during ingestion. Upload it again.' "
            "WHERE status IN ('queued', 'processing')"
        )
        return cur.rowcount


def counts(embed_model: str) -> dict:
    with get_conn() as conn:
        ready, stale, chunks = conn.execute(
            "SELECT count(*) FILTER (WHERE status = 'ready' AND embed_model = %s), "
            "count(*) FILTER (WHERE status = 'ready' AND embed_model <> %s), "
            "(SELECT count(*) FROM chunks) FROM documents",
            (embed_model, embed_model),
        ).fetchone()
    return {"ready_documents": ready, "stale_documents": stale, "chunks": chunks}


def _row(r) -> dict:
    keys = ("id", "collection_id", "filename", "status", "error", "num_chunks", "embed_model", "steps", "created_at")
    return dict(zip(keys, r, strict=True))
