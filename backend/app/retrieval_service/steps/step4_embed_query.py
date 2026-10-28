"""
STEP 4 — EMBED QUERY: turn the search query (and the original question, if different) into vectors,
with the same model used at ingestion.
"""
from app.providers import get_embedder


def embed_queries(search_query: str, question: str) -> list[list[float]]:
    queries = [search_query] if search_query.strip().lower() == question.strip().lower() else [search_query, question]
    return [get_embedder().embed_query(q) for q in queries]
