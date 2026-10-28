"""
STEP 4 — EMBED QUERY: turn the search query into a vector.

Must use the SAME embedding model and size as ingestion (EMBED_MODEL, EMBED_DIM),
otherwise the question and the chunks live in different "spaces" and can't be compared.
"""
from app.shared import gemini


def embed_query(query: str) -> list[float]:
    return gemini.embed([query], task="RETRIEVAL_QUERY")[0]
