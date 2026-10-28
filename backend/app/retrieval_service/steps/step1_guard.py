"""
STEP 1 — GUARD: cheap checks before we spend any LLM tokens.

Blocks: empty questions, very long inputs, and obvious prompt-injection attempts
("ignore your instructions..."). No LLM call — just rules, so it's instant.

Extend: detect urgent cases (e.g. "severe bleeding") and route them to a fixed
safety message, mask personal data, or add a small classifier model.
"""
import re

MAX_QUESTION_CHARS = 1000

INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above) (instructions|rules)",
    r"(reveal|show|print) (your|the) (system )?prompt",
    r"you are no longer",
    r"disregard (your|the) (rules|instructions)",
]


def guard(question: str) -> tuple[bool, str]:
    """Returns (allowed, reason)."""
    if not question.strip():
        return False, "Please type a question."
    if len(question) > MAX_QUESTION_CHARS:
        return False, f"Please keep questions under {MAX_QUESTION_CHARS} characters."
    lowered = question.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return False, "I can only answer questions about the uploaded documents."
    return True, "passed"
