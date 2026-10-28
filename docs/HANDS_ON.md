# Hands-on exercises

Do these after the [Setup Guide](SETUP_GUIDE.md), with `sample-docs/greenleaf-employee-handbook.md` uploaded.
Restart `make run` after changing `backend/.env`. Under each answer, open **How this answer was made**.

1. **Chunk size:** set `CHUNK_SIZE_WORDS=60`, upload again, and compare answers. Then try `400`.
2. **"Not found" threshold:** ask something off-topic. Try `MIN_SIMILARITY=0.3`, then `0.8`. Watch the Answer step.
3. **Follow-ups:** ask "until when?" after a question about leave. Compare `QUERY_REWRITE=true` and `false`.
4. **Keyword search:** ask for an exact word like "TravelDesk" and check how the Search step found it.
5. **Prompts:** edit `backend/app/retrieval_service/prompts/answer_system.md` (e.g. "answer in 2 sentences"). No restart needed.
6. **Languages:** ask in Hindi (or any language) about the English sample document.
7. **Collections:** create a second collection, upload a different document, and check that answers stay separate.
8. **Switch provider:** set `LLM_PROVIDER=openai` with an OpenAI key. Old documents show "upload again". Why?
9. **Build a step:** add an ingestion step between Chunk and Embed that adds keywords to each piece
   (see [Extending → Add a pipeline step](EXTENDING.md#add-a-pipeline-step)).
