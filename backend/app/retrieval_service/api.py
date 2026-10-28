"""
RETRIEVAL API: asking questions.

    POST /api/chat   {"question", "history": [{"role", "content"}], "collection_id"?}

status: answered | cached | not_found | unverified | blocked
"""
from fastapi import APIRouter

from app.retrieval_service.pipeline import answer_question
from app.retrieval_service.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["retrieval"])


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    return answer_question(body.question, [t.model_dump() for t in body.history], body.collection_id)
