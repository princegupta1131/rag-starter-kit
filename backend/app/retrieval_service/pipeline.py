"""
RETRIEVAL PIPELINE — question in, grounded answer out.

    question
      -> step1_guard         safe & sensible?            (no LLM)
      -> step2_cache         asked before?               (no LLM)
      -> step3_rewrite       typo-free standalone query  (LLM)
      -> step4_embed_query   query -> vector             (embedding)
      -> step5_retrieve      hybrid search + RRF         (Postgres)
      -> step6_answer        evidence gate, then answer  (LLM)
      -> step7_check         citations valid? else fall back safely

Every response includes `trace`: what each step did and how long it took.
"""
from app.retrieval_service.steps import step2_cache as cache
from app.retrieval_service.steps.step1_guard import guard
from app.retrieval_service.steps.step3_rewrite import rewrite
from app.retrieval_service.steps.step4_embed_query import embed_query
from app.retrieval_service.steps.step5_retrieve import hybrid_search
from app.retrieval_service.steps.step6_answer import generate_answer, has_enough_evidence
from app.retrieval_service.steps.step7_check import NOT_FOUND_MESSAGE, check_answer
from app.shared.trace import Trace


def answer_question(question: str, history: list[dict]) -> dict:
    trace = Trace()

    def respond(answer: str, status: str, sources: list | None = None, search_query: str | None = None) -> dict:
        return {"answer": answer, "status": status, "sources": sources or [],
                "search_query": search_query, "trace": trace.steps}

    with trace.step("guard") as step:
        allowed, reason = guard(question)
        step["detail"] = reason
    if not allowed:
        return respond(reason, "blocked")

    cache_key, hit = None, None
    with trace.step("cache") as step:
        if history:
            step["detail"] = "skipped (follow-up question)"
        else:
            cache_key = cache.make_key(question)
            hit = cache.get(cache_key)
            step["detail"] = "hit, returning saved answer" if hit else "miss"
    if hit:
        return {**hit, "status": "cached", "trace": trace.steps}

    with trace.step("rewrite") as step:
        search_query, step["detail"] = rewrite(question, history)

    with trace.step("embed_query") as step:
        vector = embed_query(search_query)
        step["detail"] = f"{len(vector)}-dim vector"

    with trace.step("retrieve") as step:
        hits, step["detail"] = hybrid_search(search_query, vector)

    with trace.step("answer") as step:
        enough, gate_detail = has_enough_evidence(hits)
        if enough:
            raw_answer = generate_answer(question, history, hits)
            step["detail"] = f"evidence gate passed ({gate_detail}); answered from {len(hits)} chunks"
        else:
            step["detail"] = f"evidence gate stopped it ({gate_detail}); LLM not called"
    if not enough:
        return respond(NOT_FOUND_MESSAGE, "not_found", search_query=search_query)

    with trace.step("check") as step:
        answer, sources, status, step["detail"] = check_answer(raw_answer, hits)

    response = respond(answer, status, sources, search_query)
    if cache_key and status == "answered":
        cache.put(cache_key, response)
    return response
