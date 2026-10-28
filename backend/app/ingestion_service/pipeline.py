"""
INGESTION PIPELINE — runs the 5 steps in order for one document.

    file bytes
      -> step1_extract   text out of PDF / DOCX / TXT / HTML ...
      -> step2_caption   images described by Gemini vision
      -> step3_chunk     split into overlapping pieces
      -> step4_embed     each piece -> vector
      -> step5_store     save to Postgres, mark document 'ready'

Runs in the background after upload; progress is saved in documents.steps
so the UI can show it.
"""
from psycopg.types.json import Jsonb

from app.ingestion_service.steps.step1_extract import extract
from app.ingestion_service.steps.step2_caption import caption
from app.ingestion_service.steps.step3_chunk import chunk_sections
from app.ingestion_service.steps.step4_embed import embed_chunks
from app.ingestion_service.steps.step5_store import store_chunks
from app.shared.database import get_conn
from app.shared.trace import Trace


def run_ingestion(document_id: str, filename: str, data: bytes) -> None:
    trace = Trace()
    _set_status(document_id, "processing", trace)
    try:
        with trace.step("extract") as step:
            sections = extract(filename, data)
            chars = sum(len(s["text"]) for s in sections)
            step["detail"] = f"{len(sections)} section(s), {chars:,} characters"

        with trace.step("caption") as step:
            sections, captioned = caption(filename, data, sections)
            step["detail"] = "image described by Gemini vision" if captioned else "not an image, skipped"

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
            step["detail"] = "saved to Postgres, document is now searchable"

        _save_steps(document_id, trace)
    except Exception as e:
        _set_status(document_id, "failed", trace, error=str(e))


def _set_status(document_id: str, status: str, trace: Trace, error: str | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE documents SET status = %s, error = %s, steps = %s WHERE id = %s",
            (status, error, Jsonb(trace.steps), document_id),
        )


def _save_steps(document_id: str, trace: Trace) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE documents SET steps = %s WHERE id = %s", (Jsonb(trace.steps), document_id))
