"""
Test setup. Unit tests need nothing. Tests marked `db` need TEST_DATABASE_URL:
a Postgres with pgvector whose name contains "test". It is wiped on every run.

    make test                                   # unit tests only
    TEST_DATABASE_URL=postgresql://localhost/rag_test make test   # everything
"""
import hashlib
import math
import os
import re
import socket
from pathlib import Path

from dotenv import dotenv_values

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or dotenv_values(
    Path(__file__).parent.parent / ".env"
).get("TEST_DATABASE_URL")

# Fixed settings so a developer's own .env never changes test results. Must run before `app` is imported.
os.environ.update({
    "DATABASE_URL": TEST_DATABASE_URL or "postgresql://localhost/unused_by_unit_tests",
    "LLM_PROVIDER": "gemini",
    "GEMINI_API_KEY": "test-key",
    "CHAT_MODEL": "",
    "EMBED_MODEL": "",
    "EMBED_DIM": "768",
    "MIN_SIMILARITY": "0.5",
    "CONTEXT_MARGIN": "0.12",
    "TOP_K": "6",
    "CHUNK_SIZE_WORDS": "200",
    "CHUNK_OVERLAP_WORDS": "40",
    "QUERY_REWRITE": "true",
    "STRICT_CITATIONS": "true",
    "TEXT_SEARCH_LANGUAGE": "english",
})

import pytest  # noqa: E402

from app.providers import use_providers  # noqa: E402


class FakeEmbedder:
    """Deterministic bag-of-words vectors: texts sharing words are similar. No network."""

    name = "fake-embedder"
    dim = 768

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)

    def _vec(self, text):
        v = [0.0] * self.dim
        for word in re.findall(r"\w+", text.lower()):
            v[int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dim] += 1
        norm = math.sqrt(sum(x * x for x in v)) or 1
        return [x / norm for x in v]


class FakeChat:
    """Rewrite: echoes the question. Answer: quotes source [1] with a citation. Records every call."""

    name = "fake-chat"

    def __init__(self):
        self.calls = []
        self.answer = None  # set to force a reply

    def generate(self, prompt, system=None):
        self.calls.append((prompt, system))
        if "Rewrite the user's latest question" in prompt:
            return re.search(r"Latest question: (.*)", prompt).group(1)
        if self.answer is not None:
            return self.answer
        first = re.search(r"\[1\] \(from: [^)]*\)\n(.+)", prompt)
        return f"{first.group(1).split('.')[0]} [1]." if first else "NOT_FOUND"

    def describe_image(self, data, mime_type, instruction):
        return "A diagram of the five steps of hand washing."

    def describe_video(self, data, mime_type, instruction):
        self.calls.append((mime_type, instruction))
        return "[00:05] Seema: VHSND now covers people of all ages.\nOn screen:\n[00:12] Title: What is new in VHSND"


LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


@pytest.fixture(autouse=True)
def no_internet(monkeypatch):
    """Tests must never reach a real API. Only local connections (e.g. the test database) are allowed."""
    real_connect = socket.socket.connect

    def guarded(sock, address):
        if isinstance(address, tuple) and address[0] not in LOCAL_HOSTS:
            raise RuntimeError(f"Test tried to reach the internet: {address[0]}")
        return real_connect(sock, address)

    monkeypatch.setattr(socket.socket, "connect", guarded)


@pytest.fixture
def fake_chat():
    return FakeChat()


@pytest.fixture(autouse=True)
def fake_providers(fake_chat):
    use_providers(chat=fake_chat, embedder=FakeEmbedder())
    yield
    use_providers(None, None)
