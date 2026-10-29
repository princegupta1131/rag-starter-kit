"""
The two interfaces every LLM provider implements. The rest of the app only uses these.

Add a provider: create providers/<name>.py with a ChatModel and an Embedder,
then register it in providers/__init__.py.
"""
import logging
import time
from collections.abc import Callable
from typing import Protocol, TypeVar

log = logging.getLogger(__name__)
T = TypeVar("T")

TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504}


class ProviderError(Exception):
    """The provider failed (bad key, unknown model, or still failing after retries)."""


class ChatModel(Protocol):
    name: str

    def generate(self, prompt: str, system: str | None = None) -> str:
        """Return the model's text reply."""
        ...

    def describe_image(self, data: bytes, mime_type: str, instruction: str) -> str:
        """Return a text description of an image."""
        ...


class Embedder(Protocol):
    name: str  # stored per document; search only compares vectors from the same model
    dim: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Vectors for texts being stored."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Vector for a search query."""
        ...


def with_retry(provider: str, call: Callable[[], T], attempts: int = 4) -> T:
    """Retry rate limits and temporary failures with backoff; raise ProviderError otherwise."""
    for attempt in range(attempts):
        try:
            return call()
        except Exception as e:
            if not _is_transient(e) or attempt == attempts - 1:
                raise ProviderError(f"{provider}: {_short(e)}") from e
            wait = 2 ** (attempt + 1)
            log.warning("%s temporary error (%s), retrying in %ss", provider, _short(e), wait)
            time.sleep(wait)
    raise AssertionError("unreachable")


def _is_transient(e: Exception) -> bool:
    status = getattr(e, "status_code", None) or getattr(e, "code", None)
    if isinstance(status, int):
        return status in TRANSIENT_STATUS
    return any(word in type(e).__name__ for word in ("Timeout", "Connection"))


def _short(e: Exception) -> str:
    """The provider's own message (e.g. "API key not valid"), not the whole response dump."""
    body = getattr(e, "body", None)  # OpenAI: the error object
    message = getattr(e, "message", None)  # Gemini
    if isinstance(body, dict) and isinstance(body.get("message"), str):
        text = body["message"]
    elif isinstance(message, str) and message.strip():
        text = message
    else:
        text = str(e)
    text = text.strip().splitlines()[0] if text.strip() else type(e).__name__
    status = getattr(e, "status_code", None) or getattr(e, "code", None)
    if isinstance(status, int) and str(status) not in text:
        text = f"{status} {text}"
    return text[:300]
