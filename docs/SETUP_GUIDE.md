# Setup Guide

## What you need

- **Python** 3.10+ → <https://www.python.org/downloads/>
- **Node.js** 22 (or 20.19+) → <https://nodejs.org/>
- **Git** → <https://git-scm.com/downloads>
- **Gemini API key** (free) → <https://aistudio.google.com/apikey>, or an OpenAI key
- **A Postgres database** with pgvector (see Step 2, or the [Database Setup guide](DATABASE_SETUP.md))

---

## Step 1: Get the code

```bash
git clone https://github.com/princegupta1131/rag-starter-kit.git
cd rag-starter-kit
```

---

## Step 2: Database

Use any Postgres that has **pgvector**.

**New to Postgres?** Follow the **[Database Setup guide](DATABASE_SETUP.md)**. It covers Mac, Windows,
Linux and the cloud, with pgAdmin or the terminal, and ends with your database URL.

| You have | Your database URL |
|---|---|
| Postgres with pgvector on your computer | `postgresql://USER:PASSWORD@localhost:5432/rag_starter` |
| No Postgres | free project on [Supabase](https://supabase.com) or [Neon](https://neon.tech): copy the connection string they give you |

The database and tables are created for you on the first `make check` or `make run`.
To create the tables yourself instead, run the files in `backend/sql/migrations/` in order with `psql`.

---

## Step 3: Install

```bash
make setup
```

Open `backend/.env` and fill in these 2 lines:

```env
DATABASE_URL=your-database-url
GEMINI_API_KEY=your-gemini-key
```

Using OpenAI instead? Set `LLM_PROVIDER=openai` and `OPENAI_API_KEY=your-openai-key`.

Check it:

```bash
make check
```

---

## Step 4: Run

```bash
make run
```

Open **<http://localhost:5173>**. Press **Ctrl + C** to stop.

---

## Step 5: Use it

1. Pick the **Default** collection (or create one with **+ New**)
2. Upload `sample-docs/greenleaf-employee-handbook.md`
3. Wait until it shows **READY**
4. Ask: *How many days of annual leave do I get?*

---

## Step 6 (optional): See the data in pgAdmin

Connect pgAdmin to the same database as your `DATABASE_URL`
([Database Setup → step 2](DATABASE_SETUP.md#2-install-pgadmin) shows how).
Then open **Databases** → your database (e.g. `rag_starter`) → **Schemas** → **public** → **Tables**.

| Table | What's in it |
|---|---|
| `collections` | Your knowledge bases |
| `documents` | One row per uploaded file, with its status and ingestion steps |
| `chunks` | The pieces of text, their embedding (768 numbers) and keywords |
| `schema_migrations` | Which SQL migrations have run |

Right-click a table → **View/Edit Data** → **All Rows** to see it.

**Ready-made queries:** click the database, open **Tools** → **Query Tool**, and open
`backend/sql/explore.sql`. Select one query and press **F5**. They show the chunks, the embeddings,
a meaning search and a keyword search. They only read, nothing is changed.

Don't see your database? Right-click **Databases** → **Refresh**, and check that the port matches your `DATABASE_URL`.

---

## Next time

```bash
cd rag-starter-kit
make run
```

---

## All commands

| Command | What it does |
|---|---|
| `make setup` | Install everything (first time only) |
| `make check` | Test your database and Gemini key |
| `make run` | Start the app |
| `make test` | Run the tests |

---

## Windows (no `make`)

```powershell
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
python check_setup.py
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

---

## Problems?

`make check` tells you what's wrong and how to fix it. The common ones:

| Error | Fix |
|---|---|
| `make: command not found` | Mac: run `xcode-select --install`. Windows: use the steps above |
| `Python 3.10 or newer not found` | Install Python from python.org, then `make setup` again |
| `GEMINI_API_KEY is not set` | Put your key in `backend/.env` |
| `still has the example USER:PASSWORD` | Put your real database user and password in `DATABASE_URL` |
| `API key not valid` | Copy the key again, no spaces |
| `Connection refused` | Your database isn't running |
| `"vector" is not available` | Your Postgres needs pgvector. Install it, or use Supabase / Neon |
| `address already in use` | The app is already running somewhere. Stop it, or `make run BACKEND_PORT=8001 FRONTEND_PORT=5174` |
| Red pills in the app | The backend isn't running. Run `make run` again |

Never share your `.env` file. It holds your key.
