"""
INGESTION PIPELINE: runs the steps in order for one document.

    file bytes -> extract -> caption -> chunk -> embed -> store

Runs as a FastAPI background task. Progress is saved in documents.steps for the UI.
To use a job queue (Celery, RQ, ...), call run_ingestion() from your worker instead.
"""
import logging

from app.core.trace import Trace
from app.ingestion_service.steps.step1_extract import extract
from app.ingestion_service.steps.step2_caption import caption
from app.ingestion_service.steps.step3_chunk import chunk_sections
from app.ingestion_service.steps.step4_embed import embed_chunks
from app.ingestion_service.steps.step5_store import store_chunks
from app.repositories import documents as documents_repo

log = logging.getLogger(__name__)


def run_ingestion(document_id: str, filename: str, data: bytes) -> None:
    trace = Trace()
    documents_repo.set_status(document_id, "processing", trace.steps)
    try:
        with trace.step("extract") as step:
            sections = extract(filename, data)
            chars = sum(len(s["text"]) for s in sections)
            step["detail"] = f"{len(sections)} section(s), {chars:,} characters"

        with trace.step("caption") as step:
            sections, described = caption(filename, data, sections)
            step["detail"] = {
                "image": "image described by the vision model",
                "video": "video transcribed and described by the model",
            }.get(described, "not an image or video, skipped")

        if not any(s["text"].strip() for s in sections):
            raise ValueError("No text found. Scanned PDF? Add OCR in step1_extract.py.")

        with trace.step("chunk") as step:
            chunks = chunk_sections(sections)
            words = [len(c["text"].split()) for c in chunks]
            step["detail"] = f"{len(chunks)} chunk(s), avg {sum(words) // max(len(words), 1)} words"

        with trace.step("embed") as step:
            vectors = embed_chunks(chunks)
            step["detail"] = f"{len(vectors)} vector(s) x {len(vectors[0])} dims"

        with trace.step("store") as step:
            store_chunks(document_id, chunks, vectors)
            step["detail"] = "saved, document is searchable"

        documents_repo.set_status(document_id, "ready", trace.steps)
        log.info("ingested %s: %d chunks in %d ms", filename, len(chunks), trace.total_ms)
    except Exception as e:
        log.warning("ingestion failed for %s: %s", filename, e)
        documents_repo.set_status(document_id, "failed", trace.steps, error=str(e))
