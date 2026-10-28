"""
INGESTION API — HTTP endpoints for getting content in.

    POST   /api/documents            upload one or more files
    POST   /api/documents/text       paste text directly
    GET    /api/documents            list documents + status + step log
    GET    /api/documents/{id}/chunks  see exactly how a document was chunked
    DELETE /api/documents/{id}       remove a document and its chunks

Uploads return immediately with a job id; the pipeline runs in the background.
"""
import hashlib
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.config import settings
from app.ingestion_service.pipeline import run_ingestion
from app.ingestion_service.steps.step1_extract import SUPPORTED
from app.shared.database import get_conn

router = APIRouter(prefix="/api/documents", tags=["ingestion"])


class PastedText(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1)


@router.post("")
async def upload_files(background: BackgroundTasks, files: list[UploadFile] = File(...)):
    results = []
    for upload in files:
        filename = upload.filename or "untitled.txt"
        data = await upload.read()
        results.append(_register(background, filename, data))
    return {"results": results}


@router.post("/text")
def upload_text(body: PastedText, background: BackgroundTasks):
    filename = body.title if Path(body.title).suffix.lower() in (".txt", ".md") else f"{body.title}.txt"
    return _register(background, filename, body.text.encode("utf-8"))


@router.get("")
def list_documents():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, filename, status, error, num_chunks, steps, created_at "
            "FROM documents ORDER BY created_at DESC"
        ).fetchall()
    keys = ("id", "filename", "status", "error", "num_chunks", "steps", "created_at")
    return [dict(zip(keys, row)) for row in rows]


@router.get("/{document_id}/chunks")
def list_chunks(document_id: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT chunk_index, page, content FROM chunks WHERE document_id = %s ORDER BY chunk_index",
            (document_id,),
        ).fetchall()
    return [{"index": i, "page": p, "text": t} for i, p, t in rows]


@router.delete("/{document_id}")
def delete_document(document_id: str):
    with get_conn() as conn:
        deleted = conn.execute("DELETE FROM documents WHERE id = %s RETURNING id", (document_id,)).fetchone()
    if not deleted:
        raise HTTPException(404, "Document not found")
    return {"deleted": document_id}


def _register(background: BackgroundTasks, filename: str, data: bytes) -> dict:
    """Validate, skip duplicates, create the documents row, queue the pipeline."""
    if Path(filename).suffix.lower() not in SUPPORTED:
        return {"filename": filename, "status": "rejected", "reason": f"Unsupported type. Use: {', '.join(sorted(SUPPORTED))}"}
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        return {"filename": filename, "status": "rejected", "reason": f"Larger than {settings.max_upload_mb} MB"}
    if not data.strip():
        return {"filename": filename, "status": "rejected", "reason": "File is empty"}

    content_hash = hashlib.sha256(data).hexdigest()
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id, filename, status FROM documents WHERE content_hash = %s", (content_hash,)
        ).fetchone()
        if existing and existing[2] != "failed":
            return {"filename": filename, "status": "duplicate", "id": str(existing[0]),
                    "reason": f"Same content already uploaded as '{existing[1]}'"}
        if existing:  # a failed earlier attempt: replace it
            conn.execute("DELETE FROM documents WHERE id = %s", (existing[0],))
        (document_id,) = conn.execute(
            "INSERT INTO documents (filename, content_hash) VALUES (%s, %s) RETURNING id",
            (filename, content_hash),
        ).fetchone()

    background.add_task(run_ingestion, str(document_id), filename, data)
    return {"filename": filename, "status": "queued", "id": str(document_id)}
