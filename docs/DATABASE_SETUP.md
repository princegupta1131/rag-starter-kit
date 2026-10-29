# Database Setup (Postgres + pgvector)

The app keeps your documents in **Postgres**. **pgvector** is an add-on for Postgres that stores
embeddings (lists of numbers) and finds the closest ones fast. That's the "search by meaning" part of RAG.

From this guide you need **one line** for `backend/.env`: your `DATABASE_URL`.
The app creates the database, turns on pgvector and creates the tables by itself.

## Pick your path

| You are on | Go to |
|---|---|
| **Mac** | [Mac](#mac) |
| **Windows** | [Windows](#windows) |
| **Already have Postgres and pgAdmin** (any computer) | [Already have Postgres](#already-have-postgres-and-pgadmin) |

Then: [Add it to backend/.env](#add-it-to-backendenv).

---

## Mac

Need Homebrew? Install it from <https://brew.sh>. Then run:

```bash
brew install postgresql@17 pgvector
brew services start postgresql@17
```

Postgres now runs in the background (also after a restart). No user or password needed: it uses your Mac login.

**Your line for `.env`** (copy it as is):

```env
DATABASE_URL=postgresql://localhost:5432/rag_starter
```

---

## Windows

The easiest way on Windows is a **free cloud database** from [Neon](https://neon.tech): nothing to install,
pgvector included.

1. Sign up at <https://neon.tech> and click **Create project** (any name, the region nearest to you)
2. Click **Connect** and copy the connection string. It looks like this:

   ```text
   postgresql://neondb_owner:AbC123xyz@ep-cool-river-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

**Your line for `.env`** is that whole string:

```env
DATABASE_URL=postgresql://neondb_owner:AbC123xyz@ep-cool-river-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

(Neon works the same on Mac and Linux too.)

<details>
<summary>Want Postgres on your Windows PC instead? (harder)</summary>

1. Install PostgreSQL from <https://www.postgresql.org/download/windows/>. It includes pgAdmin.
   Remember the password you choose for the `postgres` user.
2. pgvector has no Windows installer, so you build it: install
   [Visual Studio with C++](https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line?view=msvc-170#download-and-install-the-tools),
   open **x64 Native Tools Command Prompt for VS** as administrator, and run
   (change `18` to your PostgreSQL version):

   ```cmd
   set "PGROOT=C:\Program Files\PostgreSQL\18"
   cd %TEMP%
   git clone --branch v0.8.7 https://github.com/pgvector/pgvector.git
   cd pgvector
   nmake /F Makefile.win
   nmake /F Makefile.win install
   ```

3. Your line for `.env` (put your password):

   ```env
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/rag_starter
   ```

</details>

---

## Already have Postgres and pgAdmin

You can let the app do everything (just [add your line to .env](#add-it-to-backendenv)), or create the
database and tables yourself in pgAdmin to see each step.

**1. Check pgvector is installed.** In pgAdmin click your server → **Tools** → **Query Tool**, paste, press **F5**:

```sql
SELECT name, default_version FROM pg_available_extensions WHERE name = 'vector';
```

One row (`vector | 0.8.2`) means yes. No row means pgvector isn't installed on this Postgres:
Mac: `brew install pgvector`. Windows: see [Windows](#windows).

**2. Create the database.** Right-click **Databases** → **Create** → **Database…** → Database: `rag_starter` → **Save**.

**3. Turn on pgvector.** Click `rag_starter` → **Tools** → **Query Tool**, then run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**4. Create the tables.** In the same Query Tool click the **Open File** icon, open
`backend/sql/migrations/001_init.sql` and press **F5**. Then do the same with `002_collections.sql`.
Right-click **Tables** → **Refresh**: you'll see `collections`, `documents` and `chunks`.

(The app checks these files again on its first start and records them in `schema_migrations`. That's
safe: running them twice changes nothing.)

<details>
<summary>The same with the terminal (Mac / Linux)</summary>

```bash
createdb rag_starter
psql -d rag_starter -c "CREATE EXTENSION IF NOT EXISTS vector"
psql -d rag_starter -f backend/sql/migrations/001_init.sql
psql -d rag_starter -f backend/sql/migrations/002_collections.sql
psql -d rag_starter -c "\dt"
```

</details>

**5. Your line for `.env`:** build it from the fields of your pgAdmin server
(right-click it → **Properties** → **Connection**):

```text
postgresql://USERNAME:PASSWORD@HOST:PORT/rag_starter
```

| pgAdmin shows | Your line for `.env` |
|---|---|
| Username `postgres`, password `mypass123`, Host `localhost`, Port `5432` | `DATABASE_URL=postgresql://postgres:mypass123@localhost:5432/rag_starter` |
| Username `priya`, no password, Host `localhost`, Port `5432` | `DATABASE_URL=postgresql://priya@localhost:5432/rag_starter` |

If your password has `@`, `#`, `/` or `:`, it breaks the line. Change it to letters and numbers only.

---

## Add it to backend/.env

`make setup` creates the file `backend/.env`. Open it (it's hidden in Finder / Explorer, so use the terminal):

```bash
open -e backend/.env        # Mac
notepad backend\.env        # Windows
```

Change these 2 lines and save:

```env
DATABASE_URL=postgresql://localhost:5432/rag_starter
GEMINI_API_KEY=AIzaSy...your-key...
```

Get a free Gemini key at <https://aistudio.google.com/apikey>. Leave the other lines as they are.

Then check it:

```bash
make check
```

You should see:

```text
Database
  ✅ connect to DATABASE_URL  (Postgres 17.10, database created)
  ✅ pgvector extension  (vector 0.8.2)
```

Done. Continue with the [Setup Guide → Step 6](SETUP_GUIDE.md#step-6-start-the-app).

---

## See it in pgAdmin (optional, good for learning)

[pgAdmin](https://www.pgadmin.org/download/) shows your database in a window. To connect it:

1. Right-click **Servers** → **Register** → **Server…**
2. **General** tab → Name: `RAG Starter`
3. **Connection** tab, for example:

| Field | Mac | Neon (from the example string above) |
|---|---|---|
| Host | `localhost` | `ep-cool-river-123456.us-east-2.aws.neon.tech` |
| Port | `5432` | `5432` |
| Maintenance database | `postgres` | `neondb` |
| Username | your Mac username (run `whoami`) | `neondb_owner` |
| Password | leave empty | `AbC123xyz` (yours) |

4. Neon only: **Parameters** tab → **SSL mode** = `require`
5. **Save**. The tables are under **Databases** → your database → **Schemas** → **public** → **Tables**
   (after `make check` or `make run`)

### Try pgvector yourself

In the Query Tool (or `psql`):

```sql
-- two tiny "embeddings": near 0 = similar meaning, 1 = unrelated
SELECT '[1,2,3]'::vector <=> '[1,2,4]'::vector AS distance;   -- 0.009, very similar
SELECT '[1,2,3]'::vector <=> '[-3,0,1]'::vector AS distance;  -- 1.0, unrelated
```

After you upload a document, `backend/sql/explore.sql` has more queries to see the chunks and their
embeddings ([Setup Guide → see the data in pgAdmin](SETUP_GUIDE.md#optional-see-the-data-in-pgadmin)).

---

## Problems?

| Error | Fix |
|---|---|
| `Connection refused` | Postgres isn't running. Mac: `brew services start postgresql@17` |
| `"vector" is not available` | This Postgres has no pgvector. Mac: `brew install pgvector`. Windows: use Neon |
| `password authentication failed` | Wrong user or password in `DATABASE_URL`. Neon: copy the string again |
| `role "..." does not exist` | Wrong username. Mac: use the line from [Mac](#mac) exactly, with no user |
| `still has the example USER:PASSWORD` | You didn't change `DATABASE_URL` in `backend/.env` yet |
| `psql: command not found` | Use pgAdmin instead (or on a Mac: `brew link --force postgresql@17`) |

<details>
<summary>Linux: install Postgres on your computer</summary>

```bash
sudo apt install -y postgresql
ls /usr/lib/postgresql                       # your version, e.g. 16
sudo apt install -y postgresql-16-pgvector   # put your version instead of 16
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres'"
```

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_starter
```

</details>
