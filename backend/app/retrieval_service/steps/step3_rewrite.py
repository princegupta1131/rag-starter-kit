"""
STEP 3 — REWRITE: turn the user's question into a good search query.

    "wat r its side efects?"  (after a question about iron tablets)
  -> "side effects of iron tablets"

Fixes typos and resolves follow-ups so search finds the right chunks.
The ORIGINAL question is still what the LLM answers in step 6.

Prompt: prompts/rewrite.md. Turn off with QUERY_REWRITE=false to compare.
"""
from app.config import settings
from app.retrieval_service import prompts
from app.shared import gemini


def rewrite(question: str, history: list[dict]) -> tuple[str, str]:
    """Returns (search_query, detail_for_trace)."""
    if not settings.query_rewrite:
        return question, "disabled (QUERY_REWRITE=false)"
    prompt = prompts.load("rewrite", question=question, history=prompts.format_history(history))
    query = gemini.generate(prompt).strip().strip('"')
    if not query or len(query) > 500:  # model misbehaved: fall back to the original
        return question, "kept original question"
    return query, f'"{query}"'
