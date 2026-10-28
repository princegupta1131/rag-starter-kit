"""
STEP 5 — STORE & ACTIVATE: save chunks + vectors in Postgres, then mark the document ready.

Each chunk row gets two indexes automatically (see shared/database.py):
  * embedding (pgvector HNSW)  -> meaning search
  * tsv (full-text GIN)        -> keyword search
Retrieval only searches documents whose status is 'ready', so a half-written
document is never used to answer questions.
"""
import numpy as np

from app.shared.database import get_conn


def store_chunks(document_id: str, chunks: list[dict], vectors: list[list[float]]) -> None:
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
