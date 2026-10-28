from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.trace import TraceStep

Status = Literal["answered", "cached", "not_found", "unverified", "blocked"]


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[Turn] = Field(default_factory=list)
    collection_id: UUID | None = Field(default=None, description="Search one collection; omit to search all")


class Source(BaseModel):
    n: int = Field(description="The number used in the answer's [n] citations")
    document_id: UUID
    filename: str
    page: int | None
    snippet: str
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    status: Status
    sources: list[Source]
    search_query: str | None
    trace: list[TraceStep]
