"""
STEP 2 — CACHE: answer a repeated question instantly, without calling the LLM.

Key = collection + a fingerprint of its documents + the normalised question, so the
cache empties itself when documents change. Follow-up questions are never cached.

In-memory and per process. For several servers, replace this module with Redis.
"""
import time
from uuid import UUID

from app.config import settings
from app.repositories import chunks as chunks_repo

MAX_ENTRIES = 500
_store: dict[str, tuple[float, dict]] = {}


def make_key(question: str, collection_id: UUID | None) -> str:
    return f"{chunks_repo.corpus_fingerprint(collection_id)}:{' '.join(question.lower().split())}"


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


def clear() -> None:
    _store.clear()
