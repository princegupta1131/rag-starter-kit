# ingestion_service/: content in

```
upload -> step1_extract -> step2_caption -> step3_chunk -> step4_embed -> step5_store -> ready
```

| File | What it does |
|---|---|
| `api.py` | Upload files, paste text, list documents, view chunks, delete. Skips duplicates within a collection |
| `schemas.py` | Request and response types |
| `pipeline.py` | Runs the steps in order in the background and saves a step log for the UI |
| `steps/step1_extract.py` | PDF / DOCX / TXT / MD / CSV / JSON / HTML to text (keeps PDF page numbers) |
| `steps/step2_caption.py` | Images to text with the vision model |
| `steps/step3_chunk.py` | Sentence-aware chunks with overlap; drops repeats |
| `steps/step4_embed.py` | Chunks to vectors with the configured embedder |
| `steps/step5_store.py` | Saves chunks + vectors and marks the document ready, in one transaction |
