# Setup Guide

From nothing to the app running in about **20 minutes**. Do the steps **in order**.
Every step shows **Mac** and **Windows**: do only yours.

---

## Before you start: terminal basics

New to the terminal? Read this once. It saves a lot of time.

1. **Open a terminal**
   - Mac: press `Cmd + Space`, type `Terminal`, press Enter
   - Windows: press the Start key, type `cmd`, open **Command Prompt** (use this one, not PowerShell)
2. **Run a command:** copy the grey box, paste it in the terminal (Mac `Cmd + V`, Windows `Ctrl + V`
   or right-click), press **Enter**
3. **Wait** until it's finished: you see the prompt again (`%` on Mac, `>` on Windows) and can type.
   Some steps take a few minutes. Don't close the window
4. **A ❌ or red error means stop.** Read it, fix that thing, run the same command again. Don't jump ahead
5. **After installing a program, close the terminal and open a new one.** Otherwise it can't find the program
6. **Go into a folder:** type `cd ` (with a space), drag the folder from Finder / File Explorer into the
   terminal window, press Enter

---

## Step 1: Install the tools (once)

| Tool | How |
|---|---|
| **Python** (3.10 or newer) | <https://www.python.org/downloads/> → the yellow **Download** button → run the installer |
| **Node.js** | <https://nodejs.org/> → download the **LTS** version → run the installer |
| **Gemini API key** (free) | <https://aistudio.google.com/apikey> → **Create API key** → copy it into a note for later |

- **Mac:** install Python even if you already have `python3`. The one that comes with the Mac (3.9) is too old
- **Windows:** on the first screen of the Python installer, tick **Add python.exe to PATH**

**Check it** (in a **new** terminal):

| Mac | Windows |
|---|---|
| `python3 --version` | `py --version` |
| `node --version` | `node --version` |

You should see `Python 3.12` or higher (`3.13`, `3.14`… are fine) and `v22` or higher.
Mac still shows `3.9`? Close the terminal and open a new one.

---

## Step 2: Database

### Mac

1. Install Homebrew: go to <https://brew.sh>, copy the command on that page, run it.
   At the end it prints **"Next steps"** with 2 commands: **run them too**. Then open a new terminal
2. Run:

   ```bash
   brew install postgresql@17 pgvector
   brew services start postgresql@17
   ```

3. Your database line, copy it into your note:

   ```text
   DATABASE_URL=postgresql://localhost:5432/rag_starter
   ```

### Windows

We use a free cloud database, so there's nothing to install.

1. Sign up at <https://neon.tech> and click **Create project** (any name)
2. Click **Connect** and copy the connection string. It looks like
   `postgresql://neondb_owner:AbC123@ep-cool-river-123456.us-east-2.aws.neon.tech/neondb?sslmode=require`
3. Your database line is `DATABASE_URL=` followed by that string. Copy it into your note

Already have Postgres and pgAdmin, or want more options? See the [Database Setup guide](DATABASE_SETUP.md).

---

## Step 3: Get the code

1. Open <https://github.com/princegupta1131/rag-starter-kit>, click the green **Code** button →
   **Download ZIP**
2. Unzip it: Mac: double-click it. Windows: right-click → **Extract All**
3. In the terminal, go into the folder (tip 6 above). It's called `rag-starter-kit-main`

**Check you're in the right folder:** run `ls` (Mac) or `dir` (Windows). You must see `backend`,
`frontend` and `Makefile`. You don't? You're one folder too high, which happens on Windows after
Extract All: drag the `rag-starter-kit-main` folder that's **inside** it.

(Using Git? `git clone https://github.com/princegupta1131/rag-starter-kit.git` then `cd rag-starter-kit`.)

---

## Step 4: Install

### Mac

```bash
make setup
```

Wait until the last line says **Done** (2 to 5 minutes).
(`make: command not found`? Run `xcode-select --install`, then `make setup` again.)

### Windows

Paste this whole box and wait until it has finished (2 to 5 minutes):

```bat
cd backend
py -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
copy .env.example .env
cd ..\frontend
npm install
cd ..
```

Don't create `.venv` or `.env` any other way, and don't run `python main.py`: these steps do everything.

---

## Step 5: Put your database and key in the settings file

The settings live in `backend/.env`. Open it (from the main folder):

| Mac | Windows |
|---|---|
| `open -e backend/.env` | `notepad backend\.env` |

Find these **2 lines** at the top and replace them with yours from your note:

```env
DATABASE_URL=postgresql://localhost:5432/rag_starter
GEMINI_API_KEY=AIzaSyB...your-whole-key...
```

- Keep `DATABASE_URL=` and `GEMINI_API_KEY=` at the start. No spaces and no quotes around the value
- Don't change the other lines
- **Save** (Mac `Cmd + S`, Windows `Ctrl + S`) and close the file

**Check it:**

| Mac | Windows |
|---|---|
| `make check` | `backend\.venv\Scripts\python backend\check_setup.py` |

All ✅ and **"All good"**? Go on. A ❌? It says what to fix. Fix `backend/.env`, save, and check again.
It also creates the database and turns on pgvector for you.

---

## Step 6: Start the app

### Mac

```bash
make run
```

### Windows

You need **two** Command Prompt windows, both in the main folder (tip 6).

Window 1, the backend:

```bat
cd backend
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Window 2, the frontend:

```bat
cd frontend
npm run dev
```

Now open **<http://localhost:5173>** in your browser.

- **Keep the terminal window(s) open** while you use the app. Closing them stops it
- To stop: click the terminal and press `Ctrl + C`

---

## Step 7: Try it

1. Pick the **Default** collection
2. Upload `sample-docs/greenleaf-employee-handbook.md` (in the main folder)
3. Wait until it shows **READY**
4. Ask: *How many days of annual leave do I get?* The answer says 24 days, with a source

🎉 You're set up.

---

## Next time

Open a terminal, go into the main folder (tip 6), then run Step 6 again. Steps 1 to 5 are one-time only.

---

## Optional: see the data in pgAdmin

Connect [pgAdmin](https://www.pgadmin.org/download/) to your database
([how](DATABASE_SETUP.md#see-it-in-pgadmin-optional-good-for-learning)), then open **Databases** →
your database → **Schemas** → **public** → **Tables**:

| Table | What's in it |
|---|---|
| `collections` | Your knowledge bases |
| `documents` | One row per uploaded file, with its status and ingestion steps |
| `chunks` | The pieces of text, their embedding (768 numbers) and keywords |
| `schema_migrations` | Which SQL migrations have run |

Right-click a table → **View/Edit Data** → **All Rows** to see it. For ready-made queries (chunks,
embeddings, a meaning search, a keyword search), open **Tools** → **Query Tool**, open
`backend/sql/explore.sql`, select one query and press **F5**. They only read, nothing is changed.

---

## Problems?

| You see | Fix |
|---|---|
| `Python 3.10 or newer not found` / `TypeError: unsupported operand type(s) for \|` | Your Python is too old. Install a new one (Step 1), open a new terminal, run Step 4 again |
| `'py' is not recognized` (Windows) | Run the Python installer again, tick **Add python.exe to PATH**, open a new terminal |
| `node: command not found` / `'npm' is not recognized` | Install Node.js (Step 1), open a new terminal |
| `No rule to make target` / `No such file or directory` / `cannot find the path` | You're in the wrong folder. Go into the main folder (Step 3 check) |
| `Run make setup first` | Step 4 didn't finish. Run it again and wait for **Done** |
| `brew: command not found` | Run the 2 "Next steps" commands Homebrew printed, open a new terminal |
| `still has the example USER:PASSWORD` / `GEMINI_API_KEY is not set` | Step 5: put your lines in `backend/.env` and **save** |
| `API key not valid` | Copy the key again, the whole key, no spaces |
| `Connection refused` | Mac: `brew services start postgresql@17` |
| `"vector" is not available` | Mac: `brew install pgvector`. Or use the Neon database (Step 2, Windows) |
| `address already in use` | The app is already running in another window. Stop it there with `Ctrl + C` |
| Red pills / "backend not running" in the app | The backend stopped. Look at its terminal for the error, then start it again (Step 6) |

Still stuck? Copy the **whole** error message and share it.

**Never share your `backend/.env` file or your key.** Not in chat, screenshots or GitHub.
