"""OpenAI. Set LLM_PROVIDER=openai and OPENAI_API_KEY."""
import base64

from openai import OpenAI

from app.providers.base import with_retry

BATCH = 100


class OpenAIChat:
    def __init__(self, api_key: str, model: str):
        self.name = model
        self._client = OpenAI(api_key=api_key, max_retries=0)  # retries handled by with_retry

    def generate(self, prompt: str, system: str | None = None) -> str:
        result = with_retry("openai", lambda: self._client.responses.create(
            model=self.name, instructions=system, input=prompt,
        ))
        return (result.output_text or "").strip()

    def describe_image(self, data: bytes, mime_type: str, instruction: str) -> str:
        image_url = f"data:{mime_type};base64,{base64.b64encode(data).decode()}"
        result = with_retry("openai", lambda: self._client.responses.create(
            model=self.name,
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": instruction},
                    {"type": "input_image", "image_url": image_url},
                ],
            }],
        ))
        return (result.output_text or "").strip()


class OpenAIEmbedder:
    def __init__(self, api_key: str, model: str, dim: int):
        self.name = model
        self.dim = dim
        self._client = OpenAI(api_key=api_key, max_retries=0)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for i in range(0, len(texts), BATCH):
            batch = texts[i : i + BATCH]
            result = with_retry("openai", lambda b=batch: self._client.embeddings.create(
                model=self.name, input=b, dimensions=self.dim,
            ))
            vectors.extend(item.embedding for item in result.data)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
