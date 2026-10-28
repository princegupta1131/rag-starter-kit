from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.trace import TraceStep


class PastedText(BaseModel):
    collection_id: UUID
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1)


class UploadResult(BaseModel):
    filename: str
    status: Literal["queued", "duplicate", "rejected"]
    id: UUID | None = None
    reason: str | None = None


class UploadResponse(BaseModel):
    results: list[UploadResult]


class DocumentOut(BaseModel):
    id: UUID
    collection_id: UUID
    filename: str
    status: Literal["queued", "processing", "ready", "failed"]
    error: str | None
    num_chunks: int
    embed_model: str
    stale: bool = Field(description="Embedded with a different model than the current one; upload again to search it")
    steps: list[TraceStep]
    created_at: datetime


class ChunkOut(BaseModel):
    index: int
    page: int | None
    text: str
