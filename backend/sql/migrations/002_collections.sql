-- 002: collections (separate knowledge bases) + embedding model per document
--
-- Non-breaking: existing documents move into a "Default" collection and are
-- marked as embedded with gemini-embedding-001 (the only model before this change).
-- Safe to run more than once.

CREATE TABLE IF NOT EXISTS collections (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name         TEXT NOT NULL UNIQUE,
    description  TEXT NOT NULL DEFAULT '',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO collections (name, description)
VALUES ('Default', 'Your first collection')
ON CONFLICT (name) DO NOTHING;

-- every document belongs to one collection
ALTER TABLE documents ADD COLUMN IF NOT EXISTS collection_id UUID REFERENCES collections(id) ON DELETE CASCADE;
UPDATE documents SET collection_id = (SELECT id FROM collections WHERE name = 'Default') WHERE collection_id IS NULL;
ALTER TABLE documents ALTER COLUMN collection_id SET NOT NULL;
CREATE INDEX IF NOT EXISTS documents_collection_idx ON documents (collection_id);

-- the same file may now exist in different collections (still skipped within one)
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_content_hash_key;
CREATE UNIQUE INDEX IF NOT EXISTS documents_collection_hash_idx ON documents (collection_id, content_hash);

-- which embedding model produced this document's vectors; search skips other models
ALTER TABLE documents ADD COLUMN IF NOT EXISTS embed_model TEXT NOT NULL DEFAULT '';
UPDATE documents SET embed_model = 'gemini-embedding-001' WHERE embed_model = '';
