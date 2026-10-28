-- RAG Starter Kit: database schema
--
-- You do NOT need to run this. The backend runs it automatically on start.
-- Run it yourself only if you prefer to create the tables by hand:
--
--     psql "YOUR_DATABASE_URL" -f backend/sql/schema.sql
--
-- Safe to run again: it only creates what is missing.
-- Values used here are the defaults: EMBED_DIM=768 and TEXT_SEARCH_LANGUAGE=english.
-- If you change those in .env, the backend swaps them in when it runs this file.

-- pgvector: lets Postgres store and search vectors
CREATE EXTENSION IF NOT EXISTS vector;

-- One row per uploaded file
CREATE TABLE IF NOT EXISTS documents (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename      TEXT NOT NULL,
    content_hash  TEXT NOT NULL UNIQUE,              -- skips duplicate uploads
    status        TEXT NOT NULL DEFAULT 'queued',    -- queued | processing | ready | failed
    error         TEXT,
    num_chunks    INT NOT NULL DEFAULT 0,
    steps         JSONB NOT NULL DEFAULT '[]',       -- ingestion steps shown in the UI
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per searchable piece of text
CREATE TABLE IF NOT EXISTS chunks (
    id           BIGSERIAL PRIMARY KEY,
    document_id  UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index  INT NOT NULL,
    page         INT,
    content      TEXT NOT NULL,
    embedding    vector(768) NOT NULL,                                              -- meaning search
    tsv          tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED  -- keyword search
);

-- Fast search
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_tsv_idx       ON chunks USING gin (tsv);
CREATE INDEX IF NOT EXISTS chunks_document_idx  ON chunks (document_id);
