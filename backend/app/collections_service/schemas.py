from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CollectionIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)


class CollectionOut(BaseModel):
    id: UUID
    name: str
    description: str
    document_count: int
    ready_count: int
    created_at: datetime
