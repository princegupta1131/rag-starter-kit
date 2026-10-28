# retrieval_service/ — getting answers OUT

Question → grounded answer with citations, or a safe "not found".

```
question ─► 1 guard ─► 2 cache ─► 3 rewrite ─► 4 embed_query ─► 5 retrieve ─► 6 answer ─► 7 check ─► reply
            rules      seen it?   fix/complete  query → vector   vector+keyword  gate, then   citations
                                  the query                      fused (RRF)     LLM answer   valid?
```

| File | What it does |
|---|---|
| `api.py` | `POST /api/chat` endpoint |
| `pipeline.py` | Runs the 7 steps in order, stops early when a step says so, returns a `trace` |
| `steps/step1_guard.py` | Rule-based checks: empty, too long, prompt injection |
| `steps/step2_cache.py` | In-memory exact-match cache; resets automatically when documents change |
| `steps/step3_rewrite.py` | LLM rewrites the question into a standalone, typo-free search query |
| `steps/step4_embed_query.py` | Query → vector (same model as ingestion) |
| `steps/step5_retrieve.py` | Hybrid search: pgvector cosine + Postgres full-text, merged with Reciprocal Rank Fusion |
| `steps/step6_answer.py` | Evidence gate (`MIN_SIMILARITY`), then the LLM answers only from numbered sources |
| `steps/step7_check.py` | Removes fake citations; blocks uncited answers when `STRICT_CITATIONS=true` |
| `prompts/*.md` | The prompts, as plain text. **Edit these to adapt the assistant to your domain** |

## Response statuses

| status | meaning |
|---|---|
| `answered` | Answer with at least one valid citation |
| `cached` | Same question answered before (no LLM call) |
| `not_found` | Evidence gate stopped it, or the LLM said the sources don't cover it |
| `unverified` | LLM answered without citations → replaced with a safe message |
| `blocked` | Guard rejected the question |
