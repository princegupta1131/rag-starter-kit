"""
The only place that talks to Gemini.

    embed(texts, task)        -> list of vectors
    generate(prompt, system)  -> text answer
    describe_image(bytes)     -> text description of an image

Swap this file to use a different LLM provider; nothing else needs to change.
"""
import time

from google import genai
from google.genai import types

from app.config import settings

EMBED_BATCH = 50  # texts per embedding request
_client: genai.Client | None = None


def _gemini() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _with_retry(call, attempts: int = 4):
    """Retry on rate limits / temporary errors (common on free-tier keys)."""
    for attempt in range(attempts):
        try:
            return call()
        except Exception as e:  # the SDK raises different classes per version; check the message
            transient = any(code in str(e) for code in ("429", "500", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"))
            if not transient or attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt * 2)


def embed(texts: list[str], task: str) -> list[list[float]]:
    """
    task = "RETRIEVAL_DOCUMENT" when storing chunks,
           "RETRIEVAL_QUERY"    when embedding a user question.
    """
    vectors: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i : i + EMBED_BATCH]
        result = _with_retry(
            lambda: _gemini().models.embed_content(
                model=settings.embed_model,
                contents=batch,
                config=types.EmbedContentConfig(task_type=task, output_dimensionality=settings.embed_dim),
            )
        )
        vectors.extend(e.values for e in result.embeddings)
    return vectors


def generate(prompt: str, system: str | None = None, temperature: float = 0.0) -> str:
    result = _with_retry(
        lambda: _gemini().models.generate_content(
            model=settings.chat_model,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system, temperature=temperature),
        )
    )
    return (result.text or "").strip()


def describe_image(data: bytes, mime_type: str, instruction: str) -> str:
    result = _with_retry(
        lambda: _gemini().models.generate_content(
            model=settings.vision_model,
            contents=[types.Part.from_bytes(data=data, mime_type=mime_type), instruction],
            config=types.GenerateContentConfig(temperature=0.0),
        )
    )
    return (result.text or "").strip()
