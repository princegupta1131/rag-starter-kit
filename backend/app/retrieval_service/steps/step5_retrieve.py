"""
STEP 5 — RETRIEVE: hybrid search = meaning search + keyword search, fused.

  Vector search  (pgvector, cosine)   finds chunks with the same MEANING
                                      ("low blood" ~ "anaemia")
  Keyword search (Postgres full-text) finds chunks with the same WORDS
                                      (drug names, codes, acronyms)

Each search returns CANDIDATES_PER_SEARCH chunks. We merge the two ranked lists
with Reciprocal Rank Fusion (RRF):

    score(chunk) = sum over lists of 1 / (60 + rank in that list)

A chunk ranked high in both lists wins. We keep the best TOP_K.
Every result also carries its cosine `similarity` for the evidence gate in step 6.
"""
import re

import numpy as np

from app.config import settings
from app.shared.database import get_conn

RRF_K = 60

_SELECT = """
    SELECT c.id, c.content, c.page, d.filename, 1 - (c.embedding <=> %(vec)s) AS similarity
    FROM chunks c JOIN documents d ON d.id = c.document_id
    WHERE d.status = 'ready'
"""

VECTOR_SQL = _SELECT + " ORDER BY c.embedding <=> %(vec)s LIMIT %(limit)s"

KEYWORD_SQL = (
    _SELECT
    + " AND c.tsv @@ to_tsquery(%(lang)s::regconfig, %(terms)s)"
    + " ORDER BY ts_rank_cd(c.tsv, to_tsquery(%(lang)s::regconfig, %(terms)s)) DESC LIMIT %(limit)s"
)


def hybrid_search(query: str, query_vector: list[float]) -> tuple[list[dict], str]:
    """Returns (top chunks best-first, detail_for_trace)."""
    params = {"vec": np.array(query_vector, dtype=np.float32), "limit": settings.candidates_per_search,
              "lang": settings.text_search_language}
    terms = _keyword_terms(query)
    with get_conn() as conn:
        vector_rows = conn.execute(VECTOR_SQL, params).fetchall()
        keyword_rows = conn.execute(KEYWORD_SQL, {**params, "terms": terms}).fetchall() if terms else []

    fused: dict[int, dict] = {}
    for rows, source in ((vector_rows, "vector"), (keyword_rows, "keyword")):
        for rank, (chunk_id, content, page, filename, similarity) in enumerate(rows, start=1):
            hit = fused.setdefault(chunk_id, {
                "chunk_id": chunk_id, "text": content, "page": page, "filename": filename,
                "similarity": round(float(similarity), 3), "score": 0.0, "found_by": [],
            })
            hit["score"] += 1 / (RRF_K + rank)
            hit["found_by"].append(source)

    top = sorted(fused.values(), key=lambda h: h["score"], reverse=True)[: settings.top_k]
    for hit in top:
        hit["score"] = round(hit["score"], 4)
    detail = f"vector {len(vector_rows)} + keyword {len(keyword_rows)} → fused, kept top {len(top)}"
    return top, detail


def _keyword_terms(query: str) -> str:
    """'How to treat anaemia?' -> 'how | to | treat | anaemia'  (OR of words; Postgres drops stop-words)."""
    words = re.findall(r"\w{2,}", query.lower())
    return " | ".join(dict.fromkeys(words))
