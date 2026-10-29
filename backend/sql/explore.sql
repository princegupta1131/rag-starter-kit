-- Look inside the RAG database: ready-made queries for pgAdmin (or psql).
-- Read-only: nothing here changes your data.
--
-- pgAdmin: open Query Tool on your database, paste this file,
-- select ONE query (from its comment to its semicolon) and press F5.
-- Upload a document in the app first, so there is data to see.


-- 1. Collections: your separate knowledge bases
SELECT c.name,
       count(d.id)                                   AS documents,
       count(d.id) FILTER (WHERE d.status = 'ready') AS ready
FROM collections c
LEFT JOIN documents d ON d.collection_id = c.id
GROUP BY c.id
ORDER BY c.created_at;


-- 2. Documents: one row per uploaded file
SELECT d.filename, c.name AS collection, d.status, d.num_chunks, d.embed_model, d.created_at
FROM documents d
JOIN collections c ON c.id = d.collection_id
ORDER BY d.created_at DESC;


-- 3. Ingestion steps for each document (extract -> caption -> chunk -> embed -> store)
SELECT d.filename, s.step ->> 'step' AS step, s.step ->> 'detail' AS detail, s.step ->> 'ms' AS milliseconds
FROM documents d,
     jsonb_array_elements(d.steps) WITH ORDINALITY AS s(step, n)
ORDER BY d.created_at DESC, s.n;


-- 4. Chunks: the small pieces of text that get searched
SELECT d.filename,
       ch.chunk_index,
       ch.page,
       array_length(regexp_split_to_array(ch.content, '\s+'), 1) AS words,
       left(ch.content, 200)                                      AS text_start
FROM chunks ch
JOIN documents d ON d.id = ch.document_id
ORDER BY d.filename, ch.chunk_index;


-- 5. Embeddings: each chunk as a list of numbers (here: the first 5 of 768)
SELECT d.filename,
       ch.chunk_index,
       vector_dims(ch.embedding)                              AS dimensions,
       (ch.embedding::real[])[1:5]                            AS first_5_numbers,
       left(ch.content, 80)                                   AS text_start
FROM chunks ch
JOIN documents d ON d.id = ch.document_id
ORDER BY d.filename, ch.chunk_index
LIMIT 10;


-- 6. Meaning search: chunks closest in meaning to one chunk.
--    1.00 = same meaning. The app does this with your question's embedding.
--    Change the words in ILIKE to pick a different starting chunk.
WITH pick AS (
    SELECT embedding, content FROM chunks WHERE content ILIKE '%annual leave%' LIMIT 1
)
SELECT round((1 - (ch.embedding <=> pick.embedding))::numeric, 2) AS similarity,
       left(ch.content, 120)                                       AS text_start
FROM chunks ch, pick
ORDER BY ch.embedding <=> pick.embedding
LIMIT 5;


-- 7. Keyword search: what Postgres stores for keyword matching (words reduced to their root)
SELECT left(content, 60) AS text_start, left(tsv::text, 200) AS keywords
FROM chunks
LIMIT 3;


-- 8. Keyword search: chunks containing these words (change them)
SELECT ts_rank_cd(tsv, q) AS rank, left(content, 120) AS text_start
FROM chunks, to_tsquery('english', 'leave | holiday') AS q
WHERE tsv @@ q
ORDER BY rank DESC
LIMIT 5;


-- 9. Under the hood: tables, their size, and the search indexes
SELECT relname                                  AS name,
       CASE relkind WHEN 'r' THEN 'table' ELSE 'index' END AS kind,
       pg_size_pretty(pg_total_relation_size(oid)) AS size
FROM pg_class
WHERE relnamespace = 'public'::regnamespace AND relkind IN ('r', 'i')
ORDER BY kind DESC, name;


-- 10. Which migrations have run (backend/sql/migrations/)
SELECT version, applied_at FROM schema_migrations ORDER BY version;
