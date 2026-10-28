"""
STEP 3 — REWRITE: turn the question into a standalone, typo-free search query.

    "wat about its side efects?"  (after a question about iron tablets)
 -> "side effects of iron tablets"

Only used for searching; the LLM still answers the original question.
Prompt: prompts/rewrite.md. Turn off with QUERY_REWRITE=false.
"""
from app.config import settings
from app.providers import get_chat_model
from app.retrieval_service import prompts


def rewrite(question: str, history: list[dict]) -> tuple[str, str]:
    """Returns (search_query, detail_for_trace)."""
    if not settings.query_rewrite:
        return question, "disabled (QUERY_REWRITE=false)"
    prompt = prompts.load("rewrite", question=question, history=prompts.format_history(history))
    query = get_chat_model().generate(prompt).strip().strip('"')
    if not query or len(query) > 500:  # model misbehaved: fall back to the original
        return question, "kept original question"
    return query, f'"{query}"'
