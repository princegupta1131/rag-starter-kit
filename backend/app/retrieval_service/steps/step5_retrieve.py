"""
STEP 5 — RETRIEVE: hybrid search = meaning search + keyword search, fused.

  Vector search  (pgvector cosine)    finds chunks with the same meaning
  Keyword search (Postgres full-text) finds chunks with the same words (names, codes, acronyms)

Both the rewritten query and the original question are searched, so a rewrite that
drifts can't push out the right chunks. All ranked lists are merged with
Reciprocal Rank Fusion: score = sum of 1 / (60 + rank). The best TOP_K are kept, always
including the 2 chunks closest in meaning, so keyword noise can't push out the real answer.
"""
import unicodedata
from uuid import UUID

from app.config import settings
from app.providers import get_embedder
from app.repositories import chunks as chunks_repo

RRF_K = 60
KEEP_BEST_BY_MEANING = 2  # the most similar chunks are never dropped by fusion


def hybrid_search(
    search_query: str, question: str, vectors: list[list[float]], collection_id: UUID | None
) -> tuple[list[dict], str]:
    """vectors: one per query (rewritten query first). Returns (top chunks best-first, detail_for_trace)."""
    model, limit = get_embedder().name, settings.candidates_per_search
    terms = keyword_terms(f"{search_query} {question}")
    lists = [("vector", chunks_repo.vector_search(v, model, collection_id, limit)) for v in vectors]
    lists.append(("keyword", chunks_repo.keyword_search(terms, vectors[0], model, collection_id, limit)))
    top = select_top(fuse(lists), settings.top_k)
    counts = " + ".join(f"{name} {len(rows)}" for name, rows in lists)
    return top, f"{counts} → fused, kept top {len(top)}"


def fuse(ranked_lists: list[tuple[str, list[tuple]]]) -> list[dict]:
    """
    Reciprocal Rank Fusion of ranked result lists, each given as (search name, rows).
    Rows: (chunk_id, document_id, text, page, filename, similarity). Similarity is the best seen.
    """
    fused: dict[int, dict] = {}
    for source, rows in ranked_lists:
        for rank, (chunk_id, document_id, text, page, filename, similarity) in enumerate(rows, start=1):
            hit = fused.setdefault(chunk_id, {
                "chunk_id": chunk_id, "document_id": document_id, "text": text, "page": page,
                "filename": filename, "similarity": 0.0, "score": 0.0, "found_by": [],
            })
            hit["score"] += 1 / (RRF_K + rank)
            hit["similarity"] = max(hit["similarity"], round(float(similarity), 3))
            if source not in hit["found_by"]:
                hit["found_by"].append(source)
    ranked = sorted(fused.values(), key=lambda h: h["score"], reverse=True)
    for hit in ranked:
        hit["score"] = round(hit["score"], 4)
    return ranked


def select_top(ranked: list[dict], k: int) -> list[dict]:
    """The first k by fusion score, making sure the KEEP_BEST_BY_MEANING most similar chunks are among them."""
    by_meaning = sorted(ranked, key=lambda h: h["similarity"], reverse=True)[:KEEP_BEST_BY_MEANING]
    top = by_meaning + [h for h in ranked if h not in by_meaning]
    keep = {id(h) for h in top[:k]}
    return [h for h in ranked if id(h) in keep]


def keyword_terms(text: str) -> str:
    """
    'How to treat anaemia?' -> 'how | to | treat | anaemia' (OR of unique words; Postgres drops stop-words).
    Works for any script: punctuation and symbols are removed, letters and vowel signs are kept.
    """
    spaced = "".join(" " if unicodedata.category(ch)[0] in "PSZC" else ch for ch in text.lower())
    return " | ".join(dict.fromkeys(w for w in spaced.split() if len(w) >= 2))
