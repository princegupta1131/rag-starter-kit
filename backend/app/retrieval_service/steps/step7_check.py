"""
STEP 7 — CHECK & GATE: verify and tidy the answer before the user sees it.

  * NOT_FOUND from the LLM         -> friendly "not in your documents" message
  * citations like [1, 2]           -> split into [1][2]; ones that don't exist removed; repeats collapsed
  * no valid citation at all        -> with STRICT_CITATIONS=true, a safe fallback message
  * sources                         -> only the ones the answer cites, renumbered 1, 2, 3…, with clean snippets
  * two chunks quoting one sentence -> merged into one source
"""
import re

from app.config import settings

NOT_FOUND_MESSAGE = (
    "I couldn't find this in the uploaded documents. Try rephrasing, or upload a document that covers it."
)
UNVERIFIED_MESSAGE = "I found related content but couldn't give an answer backed by a specific source. Please rephrase."
CITATION = re.compile(r"\[(\d+)\]")
GROUPED_CITATION = re.compile(r"\[(\d+(?:\s*[,;]\s*\d+)+)\]")  # [1, 2] or [1;2]
PREAMBLE = re.compile(
    r"^(based on|according to) (the )?(provided |given )?(sources|context|documents)[^,:]*[,:]\s*", re.I
)
SNIPPET_CHARS = 240


def check_answer(raw_answer: str, context: list[dict], question: str) -> tuple[str, list[dict], str, str]:
    """Returns (answer, cited_sources, status, detail_for_trace)."""
    if not raw_answer.strip() or "NOT_FOUND" in raw_answer:
        return NOT_FOUND_MESSAGE, [], "not_found", "LLM said the sources don't contain the answer"

    raw_answer = split_grouped_citations(raw_answer)
    valid = set(range(1, len(context) + 1))
    cited = [int(n) for n in CITATION.findall(raw_answer)]
    invalid = sorted({n for n in cited if n not in valid})
    used = sorted({n for n in cited if n in valid})
    answer = tidy(raw_answer, valid)

    if not used:
        if settings.strict_citations:
            return UNVERIFIED_MESSAGE, [], "unverified", "no citations → blocked (STRICT_CITATIONS=true)"
        return answer, [], "answered", "no citations (STRICT_CITATIONS=false, shown anyway)"

    answer, order = renumber(answer)
    sources = [
        _source(new, context[old - 1], f"{question} {_sentences_citing(answer, new)}") for old, new in order.items()
    ]
    answer, sources, merged = merge_same_passage(answer, sources)
    detail = f"cites {', '.join(f'[{n}]' for n in used)}"
    if invalid:
        detail += f"; removed invalid {', '.join(f'[{n}]' for n in invalid)}"
    if any(old != new for old, new in order.items()):
        detail += "; renumbered " + ", ".join(f"[{old}]→[{new}]" for old, new in order.items() if old != new)
    if merged:
        detail += f"; merged {merged} source(s) quoting the same passage"
    return answer, sources, "answered", detail


def merge_same_passage(answer: str, sources: list[dict]) -> tuple[str, list[dict], int]:
    """Overlapping chunks can quote the same sentence: show it once and point both citations at it."""
    first: dict[tuple, int] = {}
    alias = {s["n"]: first.setdefault((s["document_id"], _first_sentence(s["snippet"])), s["n"]) for s in sources}
    merged = sum(1 for n, a in alias.items() if n != a)
    if not merged:
        return answer, sources, 0
    answer = CITATION.sub(lambda m: f"[{alias.get(int(m.group(1)), int(m.group(1)))}]", answer)
    answer, order = renumber(re.sub(r"(\[\d+\])(\s*\1)+", r"\1", answer))
    kept = [{**s, "n": order[s["n"]]} for s in sources if alias[s["n"]] == s["n"]]
    return answer, sorted(kept, key=lambda s: s["n"]), merged


def _first_sentence(text: str) -> str:
    return re.split(r"(?<=[.!?।])\s+", text.removeprefix("… "), maxsplit=1)[0]


def renumber(answer: str) -> tuple[str, dict[int, int]]:
    """Number citations 1, 2, 3… in order of first appearance. Returns (answer, {old: new})."""
    order: dict[int, int] = {}
    for n in CITATION.findall(answer):
        order.setdefault(int(n), len(order) + 1)
    return CITATION.sub(lambda m: f"[{order[int(m.group(1))]}]", answer), order


def split_grouped_citations(text: str) -> str:
    """[1, 2] -> [1][2], so every citation has one format."""
    return GROUPED_CITATION.sub(lambda m: "".join(f"[{n}]" for n in re.split(r"\s*[,;]\s*", m.group(1))), text)


def tidy(answer: str, valid: set[int]) -> str:
    text = CITATION.sub(lambda m: m.group(0) if int(m.group(1)) in valid else "", answer)
    text = re.sub(r"(\[\d+\])(\s*\1)+", r"\1", text)      # [1][1] -> [1]
    text = re.sub(r"[ \t]+([.,;:!?])", r"\1", text)        # gap left by a removed citation
    text = PREAMBLE.sub("", text.strip())
    return text[:1].upper() + text[1:] if text else text


def snippet(text: str, question: str, limit: int = SNIPPET_CHARS) -> str:
    """The sentence(s) of a chunk that best match `question` (question + the answer that cites it), as plain text."""
    plain = re.sub(r"[#*_`>|]+", " ", text)
    plain = re.sub(r"\s+", " ", plain).strip()
    sentences = [s for s in re.split(r"(?<=[.!?।])\s+", plain) if s]
    if not sentences:
        return plain[:limit]
    words = set(re.findall(r"\w{3,}", question.lower()))
    best = max(range(len(sentences)), key=lambda i: len(words & set(re.findall(r"\w{3,}", sentences[i].lower()))))
    out = sentences[best]
    for nxt in sentences[best + 1:]:
        if len(out) + len(nxt) + 1 > limit:
            break
        out += " " + nxt
    if len(out) > limit:
        out = out[:limit].rsplit(" ", 1)[0] + "…"
    return ("… " if best > 0 else "") + out


def _sentences_citing(answer: str, n: int) -> str:
    return " ".join(s for s in re.split(r"(?<=[.!?।])\s+|\n+", answer) if f"[{n}]" in s)


def _source(n: int, hit: dict, question: str) -> dict:
    return {
        "n": n, "document_id": hit["document_id"], "filename": hit["filename"], "page": hit["page"],
        "snippet": snippet(hit["text"], question), "similarity": hit["similarity"],
    }
