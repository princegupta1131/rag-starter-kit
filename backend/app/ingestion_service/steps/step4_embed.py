"""
STEP 4 — EMBED: turn every chunk into a vector (a list of EMBED_DIM numbers).

Chunks with similar meaning get vectors that point in a similar direction,
which is what lets step 5 of retrieval find "anaemia treatment" when the
question says "how to treat low blood".

We tell Gemini these are RETRIEVAL_DOCUMENT texts; questions are embedded
as RETRIEVAL_QUERY. The model is multilingual, so a Hindi question can match
English content.
"""
from app.shared import gemini


def embed_chunks(chunks: list[dict]) -> list[list[float]]:
    return gemini.embed([c["text"] for c in chunks], task="RETRIEVAL_DOCUMENT")
