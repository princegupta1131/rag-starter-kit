"""
STEP 4 — EMBED: turn every chunk into a vector with the configured embedding model.
Search (retrieval step 4) must use the same model, so the model name is stored per document.
"""
from app.providers import get_embedder


def embed_chunks(chunks: list[dict]) -> list[list[float]]:
    return get_embedder().embed_documents([c["text"] for c in chunks])
