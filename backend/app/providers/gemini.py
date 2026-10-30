"""Google Gemini (default). Needs GEMINI_API_KEY."""
import contextlib
import io
import time

from google import genai
from google.genai import types

from app.providers.base import ProviderError, with_retry

BATCH = 50
VIDEO_READY_TIMEOUT_S = 300  # Gemini processes an uploaded video before it can be read


class GeminiChat:
    def __init__(self, api_key: str, model: str):
        self.name = model
        self._client = genai.Client(api_key=api_key)

    def generate(self, prompt: str, system: str | None = None) -> str:
        result = with_retry("gemini", lambda: self._client.models.generate_content(
            model=self.name,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system, temperature=0.0),
        ))
        return (result.text or "").strip()

    def describe_image(self, data: bytes, mime_type: str, instruction: str) -> str:
        result = with_retry("gemini", lambda: self._client.models.generate_content(
            model=self.name,
            contents=[types.Part.from_bytes(data=data, mime_type=mime_type), instruction],
            config=types.GenerateContentConfig(temperature=0.0),
        ))
        return (result.text or "").strip()

    def describe_video(self, data: bytes, mime_type: str, instruction: str) -> str:
        """Videos are too big to send inline: upload with the Files API, wait until processed, ask, delete."""
        uploaded = with_retry("gemini", lambda: self._client.files.upload(
            file=io.BytesIO(data), config=types.UploadFileConfig(mime_type=mime_type),
        ))
        try:
            deadline = time.monotonic() + VIDEO_READY_TIMEOUT_S
            while uploaded.state == types.FileState.PROCESSING:
                if time.monotonic() > deadline:
                    raise ProviderError("gemini: the video took too long to process; try a shorter one")
                time.sleep(3)
                uploaded = with_retry("gemini", lambda name=uploaded.name: self._client.files.get(name=name))
            if uploaded.state != types.FileState.ACTIVE:
                raise ProviderError(f"gemini: couldn't process the video ({uploaded.state})")
            result = with_retry("gemini", lambda: self._client.models.generate_content(
                model=self.name,
                contents=[uploaded, instruction],
                config=types.GenerateContentConfig(temperature=0.0),
            ))
            return (result.text or "").strip()
        finally:
            with contextlib.suppress(Exception):  # Gemini also deletes uploaded files by itself after 48 hours
                self._client.files.delete(name=uploaded.name)


class GeminiEmbedder:
    def __init__(self, api_key: str, model: str, dim: int):
        self.name = model
        self.dim = dim
        self._client = genai.Client(api_key=api_key)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts, "RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY")[0]

    def _embed(self, texts: list[str], task: str) -> list[list[float]]:
        vectors: list[list[float]] = []
        for i in range(0, len(texts), BATCH):
            batch = texts[i : i + BATCH]
            result = with_retry("gemini", lambda b=batch: self._client.models.embed_content(
                model=self.name,
                contents=b,
                config=types.EmbedContentConfig(task_type=task, output_dimensionality=self.dim),
            ))
            vectors.extend(e.values for e in result.embeddings)
        return vectors
