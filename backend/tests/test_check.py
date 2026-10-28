from app.retrieval_service.steps import step7_check
from app.retrieval_service.steps.step7_check import (
    NOT_FOUND_MESSAGE,
    UNVERIFIED_MESSAGE,
    check_answer,
    snippet,
    tidy,
)

CONTEXT = [
    {"document_id": "d1", "filename": "handbook.md", "page": None, "similarity": 0.7,
     "text": "## Leave\nEvery employee gets **24 days** of paid leave. Unused days expire on 31 March."},
    {"document_id": "d2", "filename": "travel.pdf", "page": 4, "similarity": 0.6,
     "text": "Meals are reimbursed up to 1,500 rupees per day."},
]


def test_not_found_becomes_friendly_message():
    assert check_answer("NOT_FOUND", CONTEXT, "q")[:3] == (NOT_FOUND_MESSAGE, [], "not_found")


def test_returns_only_cited_sources_with_clean_snippets():
    answer, sources, status, _ = check_answer("You get 24 days [1].", CONTEXT, "how many leave days")
    assert status == "answered" and answer == "You get 24 days [1]."
    assert [s["n"] for s in sources] == [1]
    assert sources[0]["filename"] == "handbook.md"
    assert "#" not in sources[0]["snippet"] and "**" not in sources[0]["snippet"]
    assert "24 days" in sources[0]["snippet"]


def test_invalid_citations_removed_and_reported():
    answer, sources, _, detail = check_answer("Meals up to 1,500 [2] [9].", CONTEXT, "meals")
    assert answer == "Meals up to 1,500 [1]."
    assert [(s["n"], s["filename"]) for s in sources] == [(1, "travel.pdf")]
    assert "removed invalid [9]" in detail and "[2]→[1]" in detail


def test_uncited_answer_blocked_when_strict(monkeypatch):
    monkeypatch.setattr(step7_check.settings, "strict_citations", True)
    assert check_answer("You get 24 days.", CONTEXT, "q")[:3] == (UNVERIFIED_MESSAGE, [], "unverified")


def test_uncited_answer_shown_when_not_strict(monkeypatch):
    monkeypatch.setattr(step7_check.settings, "strict_citations", False)
    assert check_answer("You get 24 days.", CONTEXT, "q")[2] == "answered"


def test_grouped_citations_are_understood():
    answer, sources, status, _ = check_answer("Meals up to 1,500 rupees [1, 2].", CONTEXT, "meals")
    assert status == "answered" and answer == "Meals up to 1,500 rupees [1][2]."
    assert [s["n"] for s in sources] == [1, 2]
    assert check_answer("Meals [2;1].", CONTEXT, "q")[0] == "Meals [1][2]."


def test_snippet_follows_the_answer_not_just_the_question():
    context = [{**CONTEXT[0], "text": "Core hours are 10 to 4. Unused leave days expire on 31 March."}]
    _, sources, _, _ = check_answer("They expire on 31 March [1].", context, "until when?")
    assert sources[0]["snippet"] == "… Unused leave days expire on 31 March."


def test_tidy_collapses_repeats_and_drops_preamble():
    assert tidy("Based on the provided sources, you get 24 days [1][1] .", {1}) == "You get 24 days [1]."


def test_snippet_picks_the_most_relevant_sentence():
    text = "Intro line about the company. Laptops are given on day one. Lost laptops must be reported in 24 hours."
    assert snippet(text, "what if my laptop is lost").startswith("… Lost laptops")


def test_snippet_is_trimmed_to_limit():
    assert len(snippet("word " * 200, "word", limit=50)) <= 52


def test_sources_are_numbered_in_order_of_appearance():
    answer, sources, _, _ = check_answer("Meals [2]. Leave is 24 days [1]. Again [2].", CONTEXT, "q")
    assert answer == "Meals [1]. Leave is 24 days [2]. Again [1]."
    assert [(s["n"], s["filename"]) for s in sources] == [(1, "travel.pdf"), (2, "handbook.md")]
