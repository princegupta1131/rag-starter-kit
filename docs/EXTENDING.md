# Extending the kit

Where each kind of change goes, and the few rules that keep the code clean.

## Add an LLM provider

1. Create `backend/app/providers/<name>.py` with two classes that match the interfaces in `providers/base.py`:
   - a chat model: `generate(prompt, system)` and `describe_image(data, mime_type, instruction)`
   - an embedder: `embed_documents(texts)`, `embed_query(text)`, plus `name` and `dim`
2. Wrap API calls in `with_retry("<name>", lambda: ...)` to get retries and clean errors.
3. Register it in `providers/__init__.py` (`get_chat_model` / `get_embedder`) and add it to
   `llm_provider` and `PROVIDER_DEFAULTS` in `app/config.py`.

Embeddings from different models can't be compared, so each document stores the model that embedded it.
Search skips documents from other models and the UI marks them "upload again".

## Add a file type

In `ingestion_service/steps/step1_extract.py`: add the extension to `SUPPORTED` and a branch in `extract()`
that returns `[{"text": ..., "page": ...}]`. Add a test in `tests/test_extract.py`.

## Add a pipeline step

1. Create `steps/stepN_name.py` with one function that does one thing.
2. Call it in that service's `pipeline.py` inside a trace block:

   ```python
   with trace.step("enrich") as step:
       chunks = enrich(chunks)
       step["detail"] = f"added keywords to {len(chunks)} chunks"
   ```

The step then appears in the UI's step trace automatically.

## Change the database

1. Add the next numbered file in `backend/sql/migrations/` (e.g. `003_add_tags.sql`). Never edit an applied one.
   Use `IF NOT EXISTS` so it is safe to run twice.
2. Put the queries in `backend/app/repositories/`. Steps and APIs call repository functions, never SQL.

Migrations run on startup and are recorded in the `schema_migrations` table.

## Add an API endpoint

Add it to the service's `api.py` with request/response models from its `schemas.py`.
Raise `NotFound`, `Conflict` or `AppError` from `app/core/errors.py` for errors.
Then add the call to `frontend/src/api/client.ts` and its types to `frontend/src/types.ts`.

## Use a job queue

`ingestion_service/pipeline.py: run_ingestion(document_id, filename, data)` is a plain function.
Call it from a Celery/RQ worker instead of `background.add_task(...)` in `ingestion_service/api.py`.

## Rules

- No SQL outside `repositories/`; no provider SDK imports outside `providers/`.
- One step = one file = one job.
- New behaviour comes with a test. `make test` must stay free of network and API keys.
