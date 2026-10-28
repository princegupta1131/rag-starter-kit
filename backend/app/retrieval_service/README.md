# retrieval_service/: answers out

```
question -> guard -> cache -> rewrite -> embed_query -> retrieve -> answer -> check -> reply
```

| File | What it does |
|---|---|
| `api.py` | `POST /api/chat` |
| `schemas.py` | Request and response types |
| `pipeline.py` | Runs the steps in order, stops early when a step says so, returns a trace |
| `steps/step1_guard.py` | Rule-based checks: empty, too long, prompt injection |
| `steps/step2_cache.py` | In-memory answer cache, reset automatically when documents change |
| `steps/step3_rewrite.py` | Rewrites the question into a standalone search query |
| `steps/step4_embed_query.py` | Query to vector (same model as ingestion) |
| `steps/step5_retrieve.py` | Vector + keyword search, fused with Reciprocal Rank Fusion |
| `steps/step6_answer.py` | Evidence gate, keeps only relevant chunks, LLM answers from them |
| `steps/step7_check.py` | Removes fake citations, tidies the answer, builds clean source snippets |
| `prompts/*.md` | The prompts as plain text. Edit these to adapt the assistant to your domain |

| status | meaning |
|---|---|
| `answered` | Answer with at least one valid citation |
| `cached` | Same question answered before (no LLM call) |
| `not_found` | Nothing relevant enough, or the LLM said the sources don't cover it |
| `unverified` | The LLM answered without citations, replaced with a safe message |
| `blocked` | The guard rejected the question |
