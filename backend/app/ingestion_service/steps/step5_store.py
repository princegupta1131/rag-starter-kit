"""
STEP 5 — STORE: save chunks + vectors and mark the document ready, in one transaction.
Search only looks at 'ready' documents, so a half-written document is never used.
"""
from app.repositories import chunks as chunks_repo


def store_chunks(document_id: str, chunks: list[dict], vectors: list[list[float]]) -> None:
    chunks_repo.replace_for_document(document_id, chunks, vectors)
