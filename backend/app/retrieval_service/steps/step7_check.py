"""
STEP 7 — CHECK & GATE: verify the answer before the user sees it.

  * NOT_FOUND from the LLM          -> friendly "not in your documents" message
  * citations like [9] that don't exist -> removed
  * no valid citations at all       -> with STRICT_CITATIONS=true, fall back safely
                                       (an uncited answer can't be traced to a source)

Returns only the sources the answer actually cited, so the UI can show them.

Extend: ask a second LLM call "is every sentence supported by its source?",
or check that the answer's script/language matches the question.
"""
import re

from app.config import settings

NOT_FOUND_MESSAGE = "I couldn't find this in the uploaded documents. Try rephrasing, or upload a document that covers it."
UNVERIFIED_MESSAGE = "I found related content but couldn't produce an answer backed by a specific source. Please rephrase the question."
CITATION = re.compile(r"\[(\d+)\]")


def check_answer(raw_answer: str, hits: list[dict]) -> tuple[str, list[dict], str, str]:
    """Returns (answer, cited_sources, status, detail_for_trace)."""
    if not raw_answer or "NOT_FOUND" in raw_answer:
        return NOT_FOUND_MESSAGE, [], "not_found", "LLM said the sources don't contain the answer"

    valid = set(range(1, len(hits) + 1))
    cited = [int(n) for n in CITATION.findall(raw_answer)]
    invalid = sorted({n for n in cited if n not in valid})
    answer = CITATION.sub(lambda m: m.group(0) if int(m.group(1)) in valid else "", raw_answer)
    answer = re.sub(r"[ \t]+([.,;:])", r"\1", answer).strip()  # tidy the gap a removed citation leaves
    used = sorted({n for n in cited if n in valid})

    if not used:
        if settings.strict_citations:
            return UNVERIFIED_MESSAGE, [], "unverified", "no citations → blocked (STRICT_CITATIONS=true)"
        return answer, [], "answered", "no citations (STRICT_CITATIONS=false, shown anyway)"

    sources = [{"n": n, **_public(hits[n - 1])} for n in used]
    detail = f"cites {', '.join(f'[{n}]' for n in used)}"
    if invalid:
        detail += f"; removed invalid {', '.join(f'[{n}]' for n in invalid)}"
    return answer, sources, "answered", detail


def _public(hit: dict) -> dict:
    return {k: hit[k] for k in ("filename", "page", "text", "similarity")}
