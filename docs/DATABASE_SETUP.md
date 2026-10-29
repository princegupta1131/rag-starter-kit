# More database options

**Most people don't need this page.** The [Setup Guide, Step 2](SETUP_GUIDE.md#step-2-database) covers
Mac, Windows and "already have Postgres". Come here only for one of these:

- [Make the database and tables yourself](#make-the-database-and-tables-yourself) (to see each step)
- [Supabase](#supabase) instead of Neon
- [Linux](#linux)
- [Postgres on a Windows PC](#postgres-on-a-windows-pc) instead of Neon

---

## Make the database and tables yourself

The app does this for you on the first `make check`. To do it by hand and watch each step, in pgAdmin:

1. **Check pgvector is installed:** click your server → **Tools** → **Query Tool**, run
   `SELECT name, default_version FROM pg_available_extensions WHERE name = 'vector';`.
   One row means yes. No row: Mac `brew install pgvector`, or use Neon (Setup Guide, Step 2)
2. **Create the database:** right-click **Databases** → **Create** → **Database…** → `rag_starter` → **Save**
3. **Turn on pgvector:** click `rag_starter` → **Tools** → **Query Tool**, run `CREATE EXTENSION IF NOT EXISTS vector;`
4. **Create the tables:** in that Query Tool click **Open File**, open `backend/sql/migrations/001_init.sql`,
   press **F5**. Then the same with `002_collections.sql`. Right-click **Tables** → **Refresh**

Running them again later is safe: they change nothing the second time.

Same with the terminal (Mac / Linux), from the main folder:

```bash
createdb rag_starter
psql -d rag_starter -c "CREATE EXTENSION IF NOT EXISTS vector"
psql -d rag_starter -f backend/sql/migrations/001_init.sql
psql -d rag_starter -f backend/sql/migrations/002_collections.sql
```

---

## Supabase

1. Create a project at <https://supabase.com>. Choose a database password with only letters and numbers
2. Click **Connect** → **Session pooler** → copy the link, and put your password in place of `[YOUR-PASSWORD]`
3. `DATABASE_URL=` followed by that link

Use the **Session pooler** link: "Direct connection" doesn't work on many networks.
In pgAdmin set **Parameters** → **SSL mode** = `require`.

---

## Linux

```bash
sudo apt install -y postgresql
ls /usr/lib/postgresql                       # your version, e.g. 16
sudo apt install -y postgresql-16-pgvector   # put your version instead of 16
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres'"
```

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_starter
```

---

## Postgres on a Windows PC

Harder than Neon: pgvector has no Windows installer, so you build it.

1. Install PostgreSQL from <https://www.postgresql.org/download/windows/> (includes pgAdmin).
   Remember the password you choose for the `postgres` user
2. Install [Visual Studio with C++](https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line?view=msvc-170#download-and-install-the-tools),
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

3. `DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/rag_starter`
