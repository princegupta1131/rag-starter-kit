"""
STEP 6 — ANSWER: evidence gate first, then a reply written only from the retrieved chunks.

Evidence gate: if even the best chunk is not similar enough to the question
(similarity < MIN_SIMILARITY), we don't call the LLM at all and say "not found".
That is the main defence against made-up answers on off-topic questions.

Then the chunks are numbered [1], [2] ... and sent with the question.
Prompts: prompts/answer_system.md (the rules) and prompts/answer_user.md (the layout).
Edit those two files to adapt the assistant to any domain.
"""
from app.config import settings
from app.retrieval_service import prompts
from app.shared import gemini


def has_enough_evidence(hits: list[dict]) -> tuple[bool, str]:
    best = max((h["similarity"] for h in hits), default=0.0)
    passed = best >= settings.min_similarity
    sign = "≥" if passed else "<"
    return passed, f"best similarity {best:.2f} {sign} MIN_SIMILARITY {settings.min_similarity:.2f}"


def generate_answer(question: str, history: list[dict], hits: list[dict]) -> str:
    sources = "\n\n".join(
        f"[{n}] (from: {h['filename']}{f', page {h['page']}' if h['page'] else ''})\n{h['text']}"
        for n, h in enumerate(hits, start=1)
    )
    user_prompt = prompts.load(
        "answer_user", sources=sources, question=question, history=prompts.format_history(history)
    )
    return gemini.generate(user_prompt, system=prompts.load("answer_system"))
