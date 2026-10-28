# Setup Guide

## What you need

- **Python** 3.10+ → <https://www.python.org/downloads/>
- **Node.js** 22 → <https://nodejs.org/>
- **Git** → <https://git-scm.com/downloads>
- **Gemini API key** (free) → <https://aistudio.google.com/apikey>
- **A Postgres database** with pgvector (see Step 2)

---

## Step 1: Get the code

```bash
git clone https://github.com/princegupta1131/rag-starter-kit.git
cd rag-starter-kit
```

---

## Step 2: Database

Use any Postgres that has **pgvector**:

| You have | Do this | Your database URL |
|---|---|---|
| Your own Postgres | `createdb rag_starter` | `postgresql://USER:PASSWORD@localhost:5432/rag_starter` |
| No Postgres | free project on [Supabase](https://supabase.com) or [Neon](https://neon.tech) | copy the connection string they give you |

The tables are created automatically when the app starts.
To create them yourself instead: `psql "your-database-url" -f backend/sql/schema.sql`

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

1. Upload `sample-docs/greenleaf-employee-handbook.md`
2. Wait until it shows **READY**
3. Ask: *How many days of annual leave do I get?*

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

---

## Windows (no `make`)

```powershell
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
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

| Error | Fix |
|---|---|
| `make: command not found` | Mac: run `xcode-select --install`. Windows: use the steps above |
| `GEMINI_API_KEY is still the placeholder` | Put your key in `backend/.env` |
| `API key not valid` | Copy the key again, no spaces |
| `connection refused` | Your database isn't running |
| `extension "vector" is not available` | Your Postgres needs pgvector. Install it, or use Supabase / Neon |
| Red pills in the app | The backend isn't running. Run `make run` again |

Never share your `.env` file. It holds your key.
