"""
STEP 2 — CACHE: answer repeated questions instantly, without calling the LLM.

Key = normalised question + a fingerprint of the document set, so the cache
empties itself whenever a document is added or deleted.
Only first questions are cached; follow-ups depend on the conversation.

This is an exact-match, in-memory cache (lost on restart).
Extend: a *semantic* cache that also matches re-worded questions by embedding
similarity, or Redis to share it between servers.
"""
import time

from app.config import settings
from app.shared.database import get_conn

_store: dict[str, tuple[float, dict]] = {}
MAX_ENTRIES = 500


def make_key(question: str) -> str:
    with get_conn() as conn:
        docs, chunks = conn.execute(
            "SELECT count(*), coalesce(sum(num_chunks), 0) FROM documents WHERE status = 'ready'"
        ).fetchone()
    return f"{docs}:{chunks}:{' '.join(question.lower().split())}"


def get(key: str) -> dict | None:
    entry = _store.get(key)
    if not entry:
        return None
    saved_at, response = entry
    if time.time() - saved_at > settings.cache_ttl_seconds:
        _store.pop(key, None)
        return None
    return response


def put(key: str, response: dict) -> None:
    if len(_store) >= MAX_ENTRIES:
        _store.pop(next(iter(_store)))  # drop the oldest
    _store[key] = (time.time(), response)
