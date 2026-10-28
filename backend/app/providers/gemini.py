"""Google Gemini (default). Needs GEMINI_API_KEY."""
from google import genai
from google.genai import types

from app.providers.base import with_retry

BATCH = 50


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
