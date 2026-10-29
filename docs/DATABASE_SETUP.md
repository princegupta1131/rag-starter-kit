# Database Setup (Postgres + pgvector)

The app keeps your documents in **Postgres**. **pgvector** is a Postgres extension that adds a `vector`
column type and fast "closest meaning" search, which is the heart of RAG.

You will:

1. Install Postgres with pgvector
2. Install pgAdmin (to see the database)
3. Create the database and turn on pgvector, **with pgAdmin or the terminal**
4. Put the database URL in `backend/.env`

---

## 1. Install Postgres with pgvector

Pick **one**:

| Your computer | Use |
|---|---|
| Mac | [A. Homebrew](#a-mac-homebrew) |
| Windows | [B. Docker](#b-docker-windows-mac-linux) or [C. Cloud](#c-cloud-supabase-or-neon-no-install) |
| Linux | [D. apt](#d-linux-ubuntu--debian) or [B. Docker](#b-docker-windows-mac-linux) |
| Can't install anything | [C. Cloud](#c-cloud-supabase-or-neon-no-install) |

> **Already installed Postgres from postgresql.org?** That installer doesn't include pgvector, so the app
> will say `"vector" is not available`. Use one of the options below instead.

### A. Mac (Homebrew)

Need Homebrew? Install it from <https://brew.sh>. Then:

```bash
brew install postgresql@17 pgvector
brew services start postgresql@17
```

Postgres now runs in the background, and starts again when you restart your Mac.
Your user is your Mac username (`whoami`), with no password.

Add the Postgres commands (`psql`, `createdb`) to your terminal:

```bash
echo 'export PATH="$(brew --prefix postgresql@17)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### B. Docker (Windows, Mac, Linux)

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and open it. Then:

```bash
docker run -d --name rag-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -v rag-pgdata:/var/lib/postgresql/data pgvector/pgvector:pg17
```

This starts Postgres with pgvector already installed. Your user is `postgres`, password `postgres`
(fine on your own computer; never use it on a server). Your data is kept when you stop it.

```bash
docker start rag-postgres     # next time
docker stop rag-postgres      # stop it
```

Port 5432 already in use? Use `-p 5433:5432` and port `5433` everywhere below.

### C. Cloud: Supabase or Neon (no install)

Free, and pgvector is already available.

**Supabase**

1. Create a project at <https://supabase.com>. Choose a **database password** with only letters and numbers
   and save it
2. Click **Connect** (top of the page) → **Session pooler** → copy the URI
3. Replace `[YOUR-PASSWORD]` in it with your password

Use the **Session pooler** URI. The "Direct connection" one doesn't work on many networks.

**Neon**

1. Create a project at <https://neon.tech>
2. Click **Connect** → copy the connection string (keep the `?sslmode=require` at the end)

The database already exists (`postgres` on Supabase, `neondb` on Neon), so in step 3 skip creating it.

### D. Linux (Ubuntu / Debian)

```bash
sudo apt update
sudo apt install -y postgresql
ls /usr/lib/postgresql                            # your version, e.g. 16
sudo apt install -y postgresql-16-pgvector        # put your version instead of 16
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres'"
```

Your user is `postgres`, password `postgres`.
`Unable to locate package`? Add the official Postgres repository
(<https://www.postgresql.org/download/linux/ubuntu/>), then `sudo apt install -y postgresql-17 postgresql-17-pgvector`.

---

## 2. Install pgAdmin

Download from <https://www.pgadmin.org/download/> (Mac: or `brew install --cask pgadmin4`).

Connect it to your Postgres:

1. Open pgAdmin. Right-click **Servers** → **Register** → **Server…**
2. **General** tab → Name: `RAG Starter` (any name)
3. **Connection** tab:

| | A. Homebrew | B. Docker / D. Linux | C. Cloud |
|---|---|---|---|
| Host | `localhost` | `localhost` | from your URL (after `@`, before `:`) |
| Port | `5432` | `5432` | `5432` |
| Maintenance database | `postgres` | `postgres` | `postgres` (Neon: `neondb`) |
| Username | your Mac username | `postgres` | from your URL (before `:`) |
| Password | empty | `postgres` | your password |

4. Cloud only: **Parameters** tab → **SSL mode** = `require`
5. **Save**. Your server appears on the left

---

## 3. Create the database and turn on pgvector

Do it **one** way, pgAdmin or terminal. Both do the same thing.

(If you skip this step, the app does it for you on the first `make check`. Doing it once yourself shows
what's happening.)

### With pgAdmin

1. **Create the database** (skip on Supabase / Neon): open your server, right-click **Databases** →
   **Create** → **Database…** → Database: `rag_starter` → **Save**
2. **Turn on pgvector**: click `rag_starter`, then **Tools** → **Query Tool**, paste and press **F5**:

   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. **Check it**: run this. It should show one row with `vector` and a version like `0.8.2`:

   ```sql
   SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
   ```

4. **Try a vector**: distance between two short vectors (small number = similar meaning):

   ```sql
   SELECT '[1,2,3]'::vector <=> '[1,2,4]'::vector AS distance;
   ```

You'll also see `vector` under `rag_starter` → **Extensions** (right-click → **Refresh** if not).

### With the terminal

**A. Homebrew**

```bash
createdb rag_starter
psql -d rag_starter -c "CREATE EXTENSION IF NOT EXISTS vector"
psql -d rag_starter -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'"
```

**B. Docker** (no need to install `psql`, it runs inside the container)

```bash
docker exec rag-postgres createdb -U postgres rag_starter
docker exec rag-postgres psql -U postgres -d rag_starter -c "CREATE EXTENSION IF NOT EXISTS vector"
docker exec rag-postgres psql -U postgres -d rag_starter -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'"
```

**C. Cloud** (needs `psql`; or use pgAdmin, or the SQL editor on the website)

```bash
psql "YOUR_DATABASE_URL" -c "CREATE EXTENSION IF NOT EXISTS vector"
```

**D. Linux**

```bash
sudo -u postgres createdb rag_starter
sudo -u postgres psql -d rag_starter -c "CREATE EXTENSION IF NOT EXISTS vector"
sudo -u postgres psql -d rag_starter -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'"
```

You should see `vector | 0.8.2` (or another version).

---

## 4. Your DATABASE_URL

Put it in `backend/.env`:

| You used | `DATABASE_URL=` |
|---|---|
| A. Homebrew | `postgresql://localhost:5432/rag_starter` |
| B. Docker | `postgresql://postgres:postgres@localhost:5432/rag_starter` |
| C. Supabase / Neon | the URI you copied in step 1 |
| D. Linux | `postgresql://postgres:postgres@localhost:5432/rag_starter` |

The shape is `postgresql://USER:PASSWORD@HOST:PORT/DATABASE`.

Then check it:

```bash
make check
```

You should see `✅ connect to DATABASE_URL` and `✅ pgvector extension`. The app creates its tables
(`collections`, `documents`, `chunks`, `schema_migrations`) the first time it starts. Refresh **Tables** in
pgAdmin to see them. To look at the data, see [Setup Guide → Step 6](SETUP_GUIDE.md#step-6-optional-see-the-data-in-pgadmin).

---

## Problems?

| Error | Fix |
|---|---|
| `"vector" is not available` | This Postgres has no pgvector. Use option A, B, C or D above |
| `Connection refused` | Postgres isn't running. A: `brew services start postgresql@17`. B: `docker start rag-postgres` |
| `password authentication failed` | Wrong user or password in `DATABASE_URL` (or in pgAdmin) |
| `role "..." does not exist` | Wrong username. A: your Mac username (`whoami`). B / D: `postgres` |
| `port is already allocated` / `address already in use` | Another Postgres already uses 5432. Stop it, or use port 5433 (see B) |
| `psql: command not found` | A: run the `PATH` lines in A. B: use the `docker exec` commands. Or use pgAdmin |
| Password has `@`, `#`, `/` or `:` | It breaks the URL. Change the password to letters and numbers only |
| Supabase: `could not translate host name` / timeout | Use the **Session pooler** URI, not "Direct connection" |
| pgAdmin doesn't show `rag_starter` | Right-click **Databases** → **Refresh** |
