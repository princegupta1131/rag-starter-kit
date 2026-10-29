"""
INGESTION API: getting content in.

    POST   /api/documents                upload files (multipart: collection_id + files)
    POST   /api/documents/text           add pasted text
    GET    /api/documents?collection_id  list documents with status and step log
    GET    /api/documents/{id}/chunks    how a document was chunked
    DELETE /api/documents/{id}           remove a document and its chunks

Uploads return at once; the pipeline runs in the background (see pipeline.py).
"""
import hashlib
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from app.config import settings
from app.core.errors import NotFound
from app.ingestion_service.pipeline import run_ingestion
from app.ingestion_service.schemas import ChunkOut, DocumentOut, PastedText, UploadResponse, UploadResult
from app.ingestion_service.steps.step1_extract import SUPPORTED
from app.providers import get_embedder
from app.repositories import chunks as chunks_repo
from app.repositories import collections as collections_repo
from app.repositories import documents as documents_repo

router = APIRouter(prefix="/api/documents", tags=["ingestion"])


@router.post("", response_model=UploadResponse)
def upload_files(background: BackgroundTasks, collection_id: UUID = Form(...), files: list[UploadFile] = File(...)):
    _require_collection(collection_id)
    results = []
    for upload in files:
        data = upload.file.read(_max_bytes() + 1)  # never hold more than the limit in memory
        results.append(_register(background, collection_id, upload.filename or "untitled.txt", data))
    return {"results": results}


@router.post("/text", response_model=UploadResult)
def upload_text(body: PastedText, background: BackgroundTasks):
    _require_collection(body.collection_id)
    filename = body.title if Path(body.title).suffix.lower() in (".txt", ".md") else f"{body.title}.txt"
    return _register(background, body.collection_id, filename, body.text.encode("utf-8"))


@router.get("", response_model=list[DocumentOut])
def list_documents(collection_id: UUID | None = None):
    current = get_embedder().name
    return [
        {**doc, "stale": doc["status"] == "ready" and doc["embed_model"] != current}
        for doc in documents_repo.list_for_collection(collection_id)
    ]


@router.get("/{document_id}/chunks", response_model=list[ChunkOut])
def list_chunks(document_id: UUID):
    return chunks_repo.list_for_document(document_id)


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: UUID):
    if not documents_repo.delete(document_id):
        raise NotFound("Document not found")


def _require_collection(collection_id: UUID) -> None:
    if collections_repo.get(collection_id) is None:
        raise NotFound("Collection not found")


def _max_bytes() -> int:
    return settings.max_upload_mb * 1024 * 1024


def _register(background: BackgroundTasks, collection_id: UUID, filename: str, data: bytes) -> UploadResult:
    """Validate, skip duplicates within the collection, create the document row, queue the pipeline."""
    if Path(filename).suffix.lower() not in SUPPORTED:
        return UploadResult(filename=filename, status="rejected",
                            reason=f"Unsupported type. Use: {', '.join(sorted(SUPPORTED))}")
    if len(data) > _max_bytes():
        return UploadResult(filename=filename, status="rejected", reason=f"Larger than {settings.max_upload_mb} MB")
    if not data.strip():
        return UploadResult(filename=filename, status="rejected", reason="File is empty")

    content_hash = hashlib.sha256(data).hexdigest()
    embed_model = get_embedder().name
    existing = documents_repo.find_by_hash(collection_id, content_hash)
    if existing and existing["status"] != "failed" and existing["embed_model"] == embed_model:
        return _duplicate(filename, existing)
    if existing:  # failed before, or embedded with another model ("stale"): replace it
        documents_repo.delete(existing["id"])

    document_id = documents_repo.create(collection_id, filename, content_hash, embed_model)
    if document_id is None:  # the same file uploaded twice at the same moment
        return _duplicate(filename, documents_repo.find_by_hash(collection_id, content_hash))
    background.add_task(run_ingestion, document_id, filename, data)
    return UploadResult(filename=filename, status="queued", id=document_id)


def _duplicate(filename: str, existing: dict) -> UploadResult:
    return UploadResult(filename=filename, status="duplicate", id=existing["id"],
                        reason=f"Already in this collection as '{existing['filename']}'")
