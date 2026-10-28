"""
RETRIEVAL API — HTTP endpoint for asking questions.

    POST /api/chat   {"question": "...", "history": [{"role": "user"|"assistant", "content": "..."}]}

Returns {answer, status, sources, search_query, trace}.
status is one of: answered | cached | not_found | unverified | blocked
"""
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.retrieval_service.pipeline import answer_question

router = APIRouter(prefix="/api", tags=["retrieval"])


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[Turn] = Field(default_factory=list)


@router.post("/chat")
def chat(body: ChatRequest):
    return answer_question(body.question, [t.model_dump() for t in body.history])
