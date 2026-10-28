"""
STEP 6 — ANSWER: evidence gate, pick relevant chunks, then answer only from them.

Evidence gate: if the best chunk is less similar than MIN_SIMILARITY, stop and say
"not found" without calling the LLM.
Context: only chunks close to the best match are sent, so the answer stays on topic.
Prompts: prompts/answer_system.md (rules) and prompts/answer_user.md (layout).
"""
from app.config import settings
from app.providers import get_chat_model
from app.retrieval_service import prompts


def has_enough_evidence(hits: list[dict]) -> tuple[bool, str]:
    best = max((h["similarity"] for h in hits), default=0.0)
    passed = best >= settings.min_similarity
    sign = "≥" if passed else "<"
    return passed, f"best similarity {best:.2f} {sign} MIN_SIMILARITY {settings.min_similarity:.2f}"


def select_context(hits: list[dict]) -> list[dict]:
    """
    Keep a chunk if it is above MIN_SIMILARITY and either close to the best match (within CONTEXT_MARGIN)
    or found by keyword search too (exact terms). Always keeps the best one.
    """
    if not hits:
        return []
    best = max(hits, key=lambda h: h["similarity"])
    close = best["similarity"] - settings.context_margin
    keep = [
        h for h in hits
        if h["similarity"] >= settings.min_similarity and (h["similarity"] >= close or "keyword" in h["found_by"])
    ]
    return keep or [best]


def generate_answer(question: str, history: list[dict], context: list[dict]) -> str:
    sources = "\n\n".join(f"[{n}] (from: {_label(h)})\n{h['text']}" for n, h in enumerate(context, start=1))
    user_prompt = prompts.load(
        "answer_user", sources=sources, question=question, history=prompts.format_history(history)
    )
    return get_chat_model().generate(user_prompt, system=prompts.load("answer_system"))


def _label(hit: dict) -> str:
    return f"{hit['filename']}, page {hit['page']}" if hit["page"] else hit["filename"]
