# Setup Guide

## What you need

- **Python** 3.10+ → <https://www.python.org/downloads/>
- **Node.js** 22 → <https://nodejs.org/>
- **Git** → <https://git-scm.com/downloads>
- **Gemini API key** (free) → <https://aistudio.google.com/apikey>

---

## Step 1: Get the code

```bash
git clone https://github.com/princegupta1131/rag-starter-kit.git
cd rag-starter-kit
```

---

## Step 2: Database

You need Postgres with **pgvector**. Pick one:

**Docker** (easiest)

```bash
docker compose up -d
```

Your database URL: `postgresql://postgres:postgres@localhost:5432/rag_starter`

**Your own Postgres**

```bash
createdb rag_starter
```

Your database URL: `postgresql://USER:PASSWORD@localhost:5432/rag_starter`

**Cloud:** create a free project on [Supabase](https://supabase.com) or [Neon](https://neon.tech) and copy its connection string.

---

## Step 3: Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

> **Windows:** use `py -m venv .venv`, `.venv\Scripts\activate` and `copy .env.example .env`

Open `backend/.env` and fill in these 2 lines:

```env
DATABASE_URL=your-database-url
GEMINI_API_KEY=your-gemini-key
```

Check it, then start:

```bash
python check_setup.py
uvicorn app.main:app --reload --port 8000
```

Keep this terminal open.

---

## Step 4: Frontend

Open a **new terminal** in the `rag-starter-kit` folder:

```bash
cd frontend
npm install
npm run dev
```

Open **<http://localhost:5173>**

---

## Step 5: Use it

1. Upload `sample-docs/greenleaf-employee-handbook.md`
2. Wait until it shows **READY**
3. Ask: *How many days of annual leave do I get?*

---

## Next time

```bash
# Terminal 1
cd rag-starter-kit/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd rag-starter-kit/frontend
npm run dev
```

---

## Problems?

| Error | Fix |
|---|---|
| `Missing DATABASE_URL` | Create `backend/.env` (Step 3) |
| `connection refused` | Start Postgres or Docker |
| `extension "vector" is not available` | Use Docker, or install pgvector |
| `API key not valid` | Copy the key again, no spaces |
| `No module named ...` | Run `source .venv/bin/activate` again |
| Red pills in the app | Backend isn't running (Step 3) |

Never share your `.env` file. It holds your key.
