# ingestion_service/ — getting content IN

Upload a file → it becomes searchable chunks in Postgres.

```
upload ─► step1_extract ─► step2_caption ─► step3_chunk ─► step4_embed ─► step5_store ─► ready
          text from file   images → text    small pieces   pieces → vectors  Postgres + pgvector
```

| File | What it does |
|---|---|
| `api.py` | HTTP endpoints: upload files, paste text, list documents, view chunks, delete. Skips duplicate files (same content hash) |
| `pipeline.py` | Runs the 5 steps in order in the background and saves a step log (`documents.steps`) for the UI |
| `steps/step1_extract.py` | PDF / DOCX / TXT / MD / CSV / JSON / HTML → plain text (keeps PDF page numbers) |
| `steps/step2_caption.py` | Images (PNG / JPG / WEBP) → text description with Gemini vision |
| `steps/step3_chunk.py` | Sentence-aware chunks of `CHUNK_SIZE_WORDS` with `CHUNK_OVERLAP_WORDS` overlap; drops repeats |
| `steps/step4_embed.py` | Chunks → vectors with `EMBED_MODEL` (multilingual) |
| `steps/step5_store.py` | Writes chunks + vectors in one transaction, then marks the document `ready` |

**Add a new file type:** add a branch in `step1_extract.py` and its extension to `SUPPORTED`.
**Add a step** (e.g. tag concepts, OCR): create `steps/stepN_xxx.py` and call it in `pipeline.py` inside a `trace.step(...)` block — it will show up in the UI automatically.
