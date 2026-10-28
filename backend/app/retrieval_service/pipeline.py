"""
RETRIEVAL PIPELINE: question in, grounded answer out.

    guard -> cache -> rewrite -> embed query -> retrieve -> answer -> check

Stops early when a step says so (blocked, cached, not found).
Every response includes a trace of what each step did and how long it took.
"""
import logging
from uuid import UUID

from app.core.trace import Trace
from app.retrieval_service.steps import step2_cache as cache
from app.retrieval_service.steps.step1_guard import guard
from app.retrieval_service.steps.step3_rewrite import rewrite
from app.retrieval_service.steps.step4_embed_query import embed_queries
from app.retrieval_service.steps.step5_retrieve import hybrid_search
from app.retrieval_service.steps.step6_answer import generate_answer, has_enough_evidence, select_context
from app.retrieval_service.steps.step7_check import NOT_FOUND_MESSAGE, check_answer

log = logging.getLogger(__name__)


def answer_question(question: str, history: list[dict], collection_id: UUID | None = None) -> dict:
    trace = Trace()

    def respond(answer: str, status: str, sources: list | None = None, search_query: str | None = None) -> dict:
        log.info("chat status=%s sources=%d ms=%d", status, len(sources or []), trace.total_ms)
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
            cache_key = cache.make_key(question, collection_id)
            hit = cache.get(cache_key)
            step["detail"] = "hit, returning saved answer" if hit else "miss"
    if hit:
        return {**hit, "status": "cached", "trace": trace.steps}

    with trace.step("rewrite") as step:
        search_query, step["detail"] = rewrite(question, history)

    with trace.step("embed_query") as step:
        vectors = embed_queries(search_query, question)
        step["detail"] = f"{len(vectors)} query vector(s) x {len(vectors[0])} dims"

    with trace.step("retrieve") as step:
        hits, step["detail"] = hybrid_search(search_query, question, vectors, collection_id)

    with trace.step("answer") as step:
        enough, gate_detail = has_enough_evidence(hits)
        if enough:
            context = select_context(hits)
            raw_answer = generate_answer(question, history, context)
            step["detail"] = f"evidence gate passed ({gate_detail}); answered from {len(context)} of {len(hits)} chunks"
        else:
            step["detail"] = f"evidence gate stopped it ({gate_detail}); LLM not called"
    if not enough:
        return respond(NOT_FOUND_MESSAGE, "not_found", search_query=search_query)

    with trace.step("check") as step:
        answer, sources, status, step["detail"] = check_answer(raw_answer, context, question)

    response = respond(answer, status, sources, search_query)
    if cache_key and status == "answered":
        cache.put(cache_key, response)
    return response
