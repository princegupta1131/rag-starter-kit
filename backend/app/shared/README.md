# shared/ — code both pipelines use

| File | What it does |
|---|---|
| `database.py` | Connects to Postgres, creates the `documents` and `chunks` tables and their indexes on startup |
| `gemini.py` | The only file that calls Gemini: `embed()`, `generate()`, `describe_image()`. Swap this to change LLM provider |
| `trace.py` | Records each pipeline step (name, detail, time) so the UI can show "how it worked" |
