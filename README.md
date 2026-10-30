# RAG Starter Kit

A clean, working **RAG** (Retrieval-Augmented Generation) boilerplate: upload documents, ask questions,
get answers **from your documents, with sources**. Use it to learn RAG, or as the base for your own app.

- **Backend:** Python, FastAPI, Postgres + pgvector
- **LLM:** Gemini (default) or OpenAI, behind one interface
- **Frontend:** React + TypeScript, one page
- **You set only two things:** `DATABASE_URL` and an API key

[![CI](https://github.com/princegupta1131/rag-starter-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/princegupta1131/rag-starter-kit/actions/workflows/ci.yml)

---

## Quick start

### 👉 New here? Follow the **[Setup Guide](docs/SETUP_GUIDE.md)**

Step by step for **Mac and Windows**: tools, database, the app and pgAdmin, in about 20 minutes.

Already know Python, Node and Postgres? The short version:

```bash
git clone https://github.com/princegupta1131/rag-starter-kit.git
cd rag-starter-kit
make setup
```

Needs Python 3.10+ (Macs come with 3.9: install 3.12 from python.org) and Node 22.
Wait until `make setup` says **Done**. Then put your `DATABASE_URL` and `GEMINI_API_KEY` in `backend/.env`, and run:

```bash
make check
make run
```

Open <http://localhost:5173>. The database must be Postgres with pgvector ([options](docs/DATABASE_SETUP.md)).

---

## Features

- **Collections:** separate knowledge bases (e.g. "HR", "Product"); chat with one at a time
- **Any document:** PDF, Word, TXT, Markdown, CSV, JSON, HTML, and images (described by the vision model)
- **Hybrid search:** meaning (pgvector) + keywords (Postgres full-text), fused with RRF
- **Grounded answers:** says "not found" when nothing matches; every fact cites a source; fake citations removed
- **Clean answers:** formatted Markdown, only relevant sources, the most relevant sentence shown for each
- **Step trace:** every upload and answer shows what each pipeline step did and how long it took
- **Swappable LLM:** Gemini or OpenAI with one setting; add others with one file
- **Production basics:** connection pool, SQL migrations, typed API, one error format, logging, tests, CI

---

## How it works

### Ingestion: content in

**Upload → Extract → Caption → Chunk → Embed → Store**

| Step | What it does |
|---|---|
| 1. Extract | Gets text from PDF, Word, TXT, Markdown, CSV, JSON, HTML |
| 2. Caption | Describes images with the vision model so they become text |
| 3. Chunk | Splits text into small overlapping pieces |
| 4. Embed | Turns each piece into a vector (numbers that capture meaning) |
| 5. Store | Saves pieces + vectors in Postgres, ready to search |

### Retrieval: question to answer

**Question → Guard → Cache → Rewrite → Embed → Search → Answer → Check → Reply**

| Step | What it does |
|---|---|
| 1. Guard | Blocks empty, too long or unsafe questions |
| 2. Cache | Returns a saved answer if the question was asked before |
| 3. Rewrite | Fixes typos and completes follow-up questions |
| 4. Embed | Turns the question into a vector |
| 5. Search | Finds matching pieces by meaning **and** by keywords |
| 6. Answer | Says "not found" if nothing matches well; otherwise answers from the relevant pieces only |
| 7. Check | Keeps only real citations and returns the cited sources |

---

## Project structure

```
rag-starter-kit/
├── backend/
│   ├── app/
│   │   ├── main.py                 app entry: routers, startup, /api/health
│   │   ├── config.py               every setting and its default
│   │   ├── core/                   database pool, migrations, errors, logging, step trace
│   │   ├── providers/              LLM + embeddings: base.py (interfaces), gemini.py, openai.py
│   │   ├── repositories/           all SQL: collections, documents, chunks
│   │   ├── collections_service/    /api/collections
│   │   ├── ingestion_service/      /api/documents   (steps/step1 … step5)
│   │   └── retrieval_service/      /api/chat        (steps/step1 … step7, prompts/)
│   ├── sql/migrations/             numbered SQL files, applied on startup
│   ├── sql/explore.sql             read-only queries to look inside the database (pgAdmin)
│   ├── tests/                      unit + API tests (no API key needed)
│   └── .env.example                all settings
├── frontend/src/
│   ├── api/client.ts               typed calls to the backend
│   ├── types.ts                    response types (mirror backend schemas)
│   ├── shared/                     step trace, answer renderer
│   └── features/                   collections/, ingestion/, retrieval/
├── docs/                           setup guide, more database options, extending guide, hands-on, explainers/
└── Makefile                        setup / check / run / test / lint
```

**Rules of the codebase:** steps never write SQL (that's `repositories/`), and nothing outside
`providers/` knows which LLM is used. Each service has `api.py` (HTTP), `schemas.py` (types),
`pipeline.py` (order of steps) and `steps/` (one file per step).

---

## Configuration

All settings live in `backend/.env`; every option and its default is in [`.env.example`](backend/.env.example).

| I want to… | Change |
|---|---|
| Use OpenAI instead of Gemini | `LLM_PROVIDER=openai` and `OPENAI_API_KEY` (then upload documents again) |
| Use a different model | `CHAT_MODEL`, `EMBED_MODEL` |
| Change the assistant's rules or tone | `backend/app/retrieval_service/prompts/answer_system.md` |
| Change chunk size | `CHUNK_SIZE_WORDS`, `CHUNK_OVERLAP_WORDS` (then upload again) |
| Be stricter or looser about "not found" | `MIN_SIMILARITY` |
| Send more or fewer pieces to the LLM | `TOP_K` |

Adding a provider, file type, pipeline step or database table: **[Extending guide](docs/EXTENDING.md)**

---

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Database, provider and document counts |
| `GET` `POST` | `/api/collections` | List / create collections |
| `DELETE` | `/api/collections/{id}` | Delete a collection and its documents |
| `POST` | `/api/documents` | Upload files (`collection_id` + `files`) |
| `POST` | `/api/documents/text` | Add pasted text |
| `GET` | `/api/documents?collection_id=` | List documents and their status |
| `GET` | `/api/documents/{id}/chunks` | See a document's pieces |
| `DELETE` | `/api/documents/{id}` | Delete a document |
| `POST` | `/api/chat` | Ask a question (`question`, `history`, `collection_id`) |

Full, typed docs at <http://localhost:8000/docs> while the app runs.
Errors always look like `{"error": {"code": "not_found", "message": "..."}}`.

---

## Development

```bash
make test    # unit tests: no database, no API key, no network
make lint    # ruff + TypeScript
```

For the full API tests, create an empty database whose name contains `test` (it gets wiped) and set
`TEST_DATABASE_URL` in `backend/.env`. CI runs lint, unit tests and the frontend build on every push.

---

## Going to production

This kit includes the basics. Before serving real users, also consider:

| This kit | Add for production |
|---|---|
| No login | Authentication, and per-user access to collections |
| Background tasks inside the web server | A job queue (Celery, RQ) for large or many uploads |
| In-memory answer cache | Redis, shared by all servers |
| Text and images | OCR for scanned PDFs, speech-to-text for audio and video |
| Rule-based guard | A safety classifier for your domain |
| Tests with fake providers | An evaluation set of real questions and expected answers |

More design limits and where to change them: [Extending → Known limits](docs/EXTENDING.md#known-limits).

---

## Training

Running a workshop with this repo? See the **[hands-on exercises](docs/HANDS_ON.md)** and the
**[trainer notes](docs/TRAINER_NOTES.md)**: what to say and click at each step, a session plan, and answers to common questions.

**Interactive explainers** (open the file in your browser, after cloning or downloading the repo):

| Page | What it explains |
|---|---|
| [`docs/explainers/rag-ingestion-lab.html`](docs/explainers/rag-ingestion-lab.html) | Part 1, how a document is prepared, as 5 missions: x-ray the file, slice it into cards, the meaning galaxy, the arrow duel, save and race the index (pgvector) |
| [`docs/explainers/rag-retrieval-lab.html`](docs/explainers/rag-retrieval-lab.html) | Part 2, how a question is answered, as 9 checkpoints: the guard, the cache, the rewrite, meaning space, meaning vs words, the podium, the evidence bar, the open-book answer, the fake citation |

Both follow one example (the sample handbook and the question "Can I carry over unused holidays?"). Trainees guess first, then play to find out, and every score in them is real.

## License

[MIT](LICENSE)
