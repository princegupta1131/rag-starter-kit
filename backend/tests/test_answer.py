from app.retrieval_service.steps import step6_answer
from app.retrieval_service.steps.step6_answer import generate_answer, has_enough_evidence, select_context


def hit(similarity, found_by=("vector",)):
    return {"similarity": similarity, "found_by": list(found_by), "filename": "f.md", "page": 2, "text": "Body."}


def test_evidence_gate(monkeypatch):
    monkeypatch.setattr(step6_answer.settings, "min_similarity", 0.5)
    assert has_enough_evidence([hit(0.62), hit(0.3)])[0] is True
    assert has_enough_evidence([hit(0.49)])[0] is False
    assert has_enough_evidence([])[0] is False


def test_select_context_keeps_chunks_close_to_the_best(monkeypatch):
    monkeypatch.setattr(step6_answer.settings, "min_similarity", 0.5)
    monkeypatch.setattr(step6_answer.settings, "context_margin", 0.12)
    best, close, far, weak = hit(0.71), hit(0.62), hit(0.55), hit(0.3)
    assert select_context([best, close, far, weak]) == [best, close]


def test_select_context_keeps_exact_keyword_matches_above_the_floor(monkeypatch):
    monkeypatch.setattr(step6_answer.settings, "min_similarity", 0.5)
    monkeypatch.setattr(step6_answer.settings, "context_margin", 0.12)
    best, keyword_far, keyword_weak = hit(0.71), hit(0.52, ("vector", "keyword")), hit(0.4, ("keyword",))
    assert select_context([best, keyword_far, keyword_weak]) == [best, keyword_far]


def test_select_context_always_keeps_the_best(monkeypatch):
    monkeypatch.setattr(step6_answer.settings, "min_similarity", 0.9)
    only = hit(0.6)
    assert select_context([only]) == [only]


def test_generate_answer_sends_numbered_sources_and_rules(fake_chat):
    generate_answer("What dose?", [], [hit(0.7)])
    prompt, system = fake_chat.calls[-1]
    assert "[1] (from: f.md, page 2)\nBody." in prompt
    assert "Question: What dose?" in prompt
    assert "NOT_FOUND" in system
