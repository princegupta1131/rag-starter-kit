"""
STEP 3 — CHUNK: split long text into small, searchable pieces.

Why: an embedding of a whole 50-page PDF is too blurry to match a specific question,
and the LLM can only read a limited amount. Small pieces = precise search.

How (sentence-aware sliding window):
  1. Split text into sentences.
  2. Add sentences to a chunk until it reaches CHUNK_SIZE_WORDS.
  3. Start the next chunk with the last ~CHUNK_OVERLAP_WORDS words, so an idea that
     crosses a boundary is still found.
  4. Skip exact duplicate chunks (e.g. repeated headers/footers).

Try in the hands-on: change CHUNK_SIZE_WORDS (100 vs 400) and compare answers.
"""
import hashlib
import re

from app.config import settings

SENTENCE_END = re.compile(r"(?<=[.!?।])\s+|\n\s*\n")


def chunk_sections(sections: list[dict], size: int | None = None, overlap: int | None = None) -> list[dict]:
    size = size or settings.chunk_size_words
    overlap = settings.chunk_overlap_words if overlap is None else overlap

    chunks: list[dict] = []
    seen: set[str] = set()
    for section in sections:
        for text in _window(_sentences(section["text"], size), size, overlap):
            fingerprint = hashlib.sha1(" ".join(text.lower().split()).encode()).hexdigest()
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            chunks.append({"index": len(chunks), "page": section["page"], "text": text})
    return chunks


def _sentences(text: str, size: int) -> list[str]:
    """Split into sentences; any sentence longer than a whole chunk is cut by words."""
    out: list[str] = []
    for sentence in SENTENCE_END.split(text):
        words = sentence.split()
        for i in range(0, len(words), size):
            out.append(" ".join(words[i : i + size]))
    return [s for s in out if s]


def _window(sentences: list[str], size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for sentence in sentences:
        n = len(sentence.split())
        if current and current_words + n > size:
            chunks.append(" ".join(current))
            # carry the tail of this chunk into the next one
            tail: list[str] = []
            tail_words = 0
            for s in reversed(current):
                if tail_words + len(s.split()) > overlap:
                    break
                tail.insert(0, s)
                tail_words += len(s.split())
            if tail_words + n > size:  # no room for overlap next to a very long sentence
                tail, tail_words = [], 0
            current, current_words = tail, tail_words
        current.append(sentence)
        current_words += n
    if current:
        chunks.append(" ".join(current))
    return chunks
