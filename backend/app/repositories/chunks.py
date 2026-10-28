"""SQL for the chunks table: storing them and the two searches (vector + keyword)."""
from uuid import UUID

import numpy as np

from app.config import settings
from app.core.database import get_conn


def replace_for_document(document_id: str, chunks: list[dict], vectors: list[list[float]]) -> None:
    """Write all chunks of a document and mark it ready, in one transaction."""
    rows = [
        (document_id, c["index"], c["page"], c["text"], np.array(v, dtype=np.float32))
        for c, v in zip(chunks, vectors, strict=True)
    ]
    with get_conn() as conn, conn.transaction():
        conn.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO chunks (document_id, chunk_index, page, content, embedding) VALUES (%s, %s, %s, %s, %s)",
                rows,
            )
        conn.execute(
            "UPDATE documents SET status = 'ready', num_chunks = %s, error = NULL WHERE id = %s",
            (len(rows), document_id),
        )


def list_for_document(document_id: UUID) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT chunk_index, page, content FROM chunks WHERE document_id = %s ORDER BY chunk_index",
            (document_id,),
        ).fetchall()
    return [{"index": i, "page": p, "text": t} for i, p, t in rows]


# Both searches return rows of (chunk_id, document_id, content, page, filename, similarity),
# only from ready documents embedded with the current model, optionally in one collection.
_SELECT = """
    SELECT c.id, d.id, c.content, c.page, d.filename, 1 - (c.embedding <=> %(vec)s) AS similarity
    FROM chunks c JOIN documents d ON d.id = c.document_id
    WHERE d.status = 'ready' AND d.embed_model = %(embed_model)s
      AND (%(collection)s::uuid IS NULL OR d.collection_id = %(collection)s::uuid)
"""


def vector_search(vector: list[float], embed_model: str, collection_id: UUID | None, limit: int) -> list[tuple]:
    with get_conn() as conn:
        return conn.execute(
            _SELECT + " ORDER BY c.embedding <=> %(vec)s LIMIT %(limit)s",
            _params(vector, embed_model, collection_id, limit),
        ).fetchall()


def keyword_search(
    terms: str, vector: list[float], embed_model: str, collection_id: UUID | None, limit: int
) -> list[tuple]:
    """terms is a Postgres tsquery string such as 'leave | carry | over'."""
    if not terms:
        return []
    params = _params(vector, embed_model, collection_id, limit) | {
        "terms": terms, "lang": settings.text_search_language,
    }
    with get_conn() as conn:
        return conn.execute(
            _SELECT
            + " AND c.tsv @@ to_tsquery(%(lang)s::regconfig, %(terms)s)"
            + " ORDER BY ts_rank_cd(c.tsv, to_tsquery(%(lang)s::regconfig, %(terms)s)) DESC LIMIT %(limit)s",
            params,
        ).fetchall()


def corpus_fingerprint(collection_id: UUID | None) -> str:
    """Changes whenever searchable content changes; used as part of the answer cache key."""
    with get_conn() as conn:
        docs, chunks = conn.execute(
            "SELECT count(*), coalesce(sum(num_chunks), 0) FROM documents "
            "WHERE status = 'ready' AND (%s::uuid IS NULL OR collection_id = %s::uuid)",
            (collection_id, collection_id),
        ).fetchone()
    return f"{collection_id or 'all'}:{docs}:{chunks}"


def _params(vector: list[float], embed_model: str, collection_id: UUID | None, limit: int) -> dict:
    return {
        "vec": np.array(vector, dtype=np.float32),
        "embed_model": embed_model,
        "collection": str(collection_id) if collection_id else None,
        "limit": limit,
    }
