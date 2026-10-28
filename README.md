# RAG Starter Kit

A lightweight, end-to-end **Retrieval-Augmented Generation** app for learning and hands-on practice.
Upload any documents, ask questions, get answers **grounded in your content with citations**, or a safe "not found".

- **Backend:** Python · FastAPI · Postgres + pgvector · Gemini
- **Frontend:** React (Vite), one page
- **You configure only two things:** `DATABASE_URL` and `GEMINI_API_KEY`

> **New here? Follow the simple [Setup Guide](docs/SETUP_GUIDE.md).**

```
INGESTION · content in                                         (backend/app/ingestion_service)
 upload ─► 1 extract ─► 2 caption ─► 3 chunk ─► 4 embed ─► 5 store & activate
           PDF/DOCX/     images →     sentence-   Gemini      Postgres: pgvector
           TXT/HTML      text         aware +     embeddings  + full-text index
                         (vision)     overlap

RETRIEVAL · question → grounded answer                         (backend/app/retrieval_service)
 question ─► 1 guard ─► 2 cache ─► 3 rewrite ─► 4 embed query ─► 5 retrieve ─► 6 answer ─► 7 check & gate
             rules      seen it?   typos +      same model as    vector +       evidence    citations valid?
                                   follow-ups   ingestion        keyword, RRF   gate, then  else fall back
                                                                                LLM answer  safely
```

Every upload and every answer comes with a **step-by-step trace** in the UI, so you can see what each stage did and how long it took.

---

## 1. Prerequisites

| Need | Version | Check |
|---|---|---|
| Python | 3.10+ | `python3 --version` |
| Node.js | 20.19+ | `node --version` |
| Postgres with **pgvector** | any recent | see options below |
| Gemini API key | free | <https://aistudio.google.com/apikey> |

**Postgres options (pick one):**
- **Already have one?** Make sure the `vector` extension is available (`CREATE EXTENSION vector;` works).
- **Cloud (free tiers):** Supabase, Neon, or any managed Postgres that supports pgvector. Copy its connection string.

## 2. Setup (about 5 minutes)

```bash
git clone https://github.com/princegupta1131/rag-starter-kit.git
cd rag-starter-kit
make setup
```

Open `backend/.env` and set your two values:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
GEMINI_API_KEY=your-key
```

Then:

```bash
make check     # tests the database + Gemini key
make run       # starts backend (:8000) + frontend (:5173); Ctrl+C stops both
```

Open <http://localhost:5173>. Both pills in the top-right should be green.
Tables are created automatically on first start. API docs: <http://localhost:8000/docs>

No `make` (Windows)? See the manual steps in the [Setup Guide](docs/SETUP_GUIDE.md#windows-no-make).

## 3. Try it

1. Upload `sample-docs/greenleaf-employee-handbook.md` (or any PDF / DOCX / TXT / image of your own).
2. Click the document name to watch its 5 ingestion steps, then **View chunks**.
3. Ask the questions listed at the bottom of the sample document.
4. Under each answer, open **How this answer was made** to see all 7 retrieval steps.

---

## 4. Folder map: what does what

```
rag-starter-kit/
├── backend/
│   ├── .env.example                  the only config file (2 required values)
│   ├── check_setup.py                verifies DB + Gemini before you start
│   ├── requirements.txt
│   └── app/
│       ├── main.py                   starts FastAPI, mounts both services, /api/health
│       ├── config.py                 every setting + its default
│       ├── shared/                   used by both pipelines
│       │   ├── database.py           connection + table/index creation
│       │   ├── gemini.py             the ONLY file that calls the LLM / embeddings
│       │   └── trace.py              records each step for the UI
│       ├── ingestion_service/        CONTENT IN
│       │   ├── api.py                upload / paste / list / chunks / delete endpoints
│       │   ├── pipeline.py           runs the 5 steps in order
│       │   └── steps/
│       │       ├── step1_extract.py
│       │       ├── step2_caption.py
│       │       ├── step3_chunk.py
│       │       ├── step4_embed.py
│       │       └── step5_store.py
│       └── retrieval_service/        ANSWERS OUT
│           ├── api.py                POST /api/chat
│           ├── pipeline.py           runs the 7 steps in order
│           ├── prompts/              plain-text prompts — edit to change behaviour
│           │   ├── answer_system.md  the grounding rules
│           │   ├── answer_user.md    how sources + question are laid out
│           │   └── rewrite.md        query-rewrite instructions
│           └── steps/
│               ├── step1_guard.py
│               ├── step2_cache.py
│               ├── step3_rewrite.py
│               ├── step4_embed_query.py
│               ├── step5_retrieve.py
│               ├── step6_answer.py
│               └── step7_check.py
├── frontend/
│   └── src/
│       ├── App.jsx                   page layout
│       ├── api/client.js             all backend calls
│       ├── shared/StepTrace.jsx      trace view used by both panels
│       └── features/
│           ├── ingestion/            left panel  ↔ ingestion_service
│           └── retrieval/            right panel ↔ retrieval_service
├── docs/SETUP_GUIDE.md               short step-by-step setup
├── sample-docs/                      a practice document + questions
└── Makefile                          make setup / check / run
```

Each `steps/stepN_*.py` file starts with a short explanation of **what** the step does and **why**.
`ingestion_service/README.md` and `retrieval_service/README.md` summarise each service on one page.

## 5. Where to change what

| I want to… | Change |
|---|---|
| Use a different Gemini model | `CHAT_MODEL` / `EMBED_MODEL` in `.env` |
| Use OpenAI / Claude / a local model | rewrite the 3 functions in `shared/gemini.py` |
| Support a new file type | `ingestion_service/steps/step1_extract.py` |
| Change chunk size | `CHUNK_SIZE_WORDS`, `CHUNK_OVERLAP_WORDS` in `.env` (re-upload documents) |
| Make the bot stricter / looser on "not found" | `MIN_SIMILARITY` in `.env` |
| Change the assistant's tone, rules or domain | `retrieval_service/prompts/answer_system.md` |
| Send more / fewer chunks to the LLM | `TOP_K` in `.env` |
| Add a safety rule | `retrieval_service/steps/step1_guard.py` |
| Add a pipeline step | new `steps/stepN_name.py` + one `with trace.step(...)` block in that service's `pipeline.py` |

## 6. Hands-on exercises

1. **Chunk size.** Set `CHUNK_SIZE_WORDS=60`, restart, re-upload, view chunks. Ask the same questions. What got better or worse? Try `400`.
2. **Evidence gate.** Ask something off-topic and read the `answer` step in the trace. Set `MIN_SIMILARITY=0.3`, then `0.8`. What changes?
3. **Query rewrite.** Ask a follow-up ("until when?"). Compare `QUERY_REWRITE=true` vs `false` in the trace's *search query*.
4. **Hybrid search.** In the `retrieve` step, how many hits came from vector vs keyword? Ask for an exact term (e.g. "TravelDesk") and check which search found it.
5. **Prompt engineering.** Edit `prompts/answer_system.md`: "answer in at most 2 sentences" or "always answer as bullet points". Prompts are re-read on every question, so no restart needed.
6. **Citations gate.** Set `STRICT_CITATIONS=false` and remove rule 2 from the system prompt. What can go wrong?
7. **Multilingual.** Ask in Hindi (or any language) about an English document.
8. **Build a step.** Add an *enrich* step to ingestion, between chunk and embed, that asks Gemini for 5 keywords per chunk and adds them to the chunk text. Does retrieval improve?

## 7. API reference

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | DB status, key set, models, counts |
| POST | `/api/documents` | Upload files (multipart field `files`, multiple allowed) |
| POST | `/api/documents/text` | `{"title", "text"}` |
| GET | `/api/documents` | List with status + ingestion steps |
| GET | `/api/documents/{id}/chunks` | Chunks of one document |
| DELETE | `/api/documents/{id}` | Delete a document and its chunks |
| POST | `/api/chat` | `{"question", "history": [{"role", "content"}]}` → `{answer, status, sources, search_query, trace}` |

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `Missing DATABASE_URL, GEMINI_API_KEY` | You didn't create `backend/.env`. Run `cp .env.example .env` and fill it in |
| `extension "vector" is not available` | Your Postgres doesn't have pgvector. Install it, or use a free Supabase / Neon database |
| `permission denied to create extension` | Ask your DB admin to run `CREATE EXTENSION vector;` once, or use a DB you own |
| `chunks.embedding is vector(…) but EMBED_DIM=…` | You changed `EMBED_DIM` after first start. Run `DROP TABLE chunks, documents;` and restart |
| `429` / `RESOURCE_EXHAUSTED` | Free-tier rate limit. The app retries automatically; for big files wait a minute and retry |
| `404 … model not found` | Model name changed. Pick a current one from <https://ai.google.dev/gemini-api/docs/models> and set `CHAT_MODEL` |
| Pills red in the UI | Backend not running on port 8000, or check its terminal for errors |
| Every answer is "not found" | `MIN_SIMILARITY` too high for your content. Look at "best similarity" in the trace and lower it |
| PDF gives "No text found" | It's a scanned PDF (images only). Add OCR in `step1_extract.py`, or upload page images instead |

## 9. From starter to production

This kit keeps each stage as small as possible. A production RAG usually adds:

| Starter kit | Production |
|---|---|
| FastAPI background task | job queue (Celery / Redis) for big batches and retries |
| Text extraction only | OCR for scans, Whisper for audio / video |
| Gemini embeddings (API) | same, or a self-hosted multilingual model (e.g. BGE-M3) |
| Exact-match in-memory cache | semantic cache in Redis |
| Rule-based guard | language detection + classifier for urgent / unsafe questions |
| Citation check | grounding verification + script / language check + confidence score |
| Manual testing | a gold question set run on every change (evaluation) |
