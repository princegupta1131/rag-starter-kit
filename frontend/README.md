# frontend/ — one-page React UI

```
src/
├── App.jsx                     page layout: left panel + right panel + health pills
├── api/client.js               every backend call in one place
├── shared/StepTrace.jsx        renders a pipeline trace (used by both panels)
└── features/
    ├── ingestion/              LEFT panel  → backend ingestion_service
    │   ├── IngestionPanel.jsx  upload files / paste text, document list, polling
    │   └── DocumentCard.jsx    one document: status, step log, chunks, delete
    └── retrieval/              RIGHT panel → backend retrieval_service
        ├── ChatPanel.jsx       conversation + question box
        └── AnswerMessage.jsx   answer with [n] citations, sources, "how this answer was made"
```

`vite.config.js` forwards `/api/*` to `http://localhost:8000`, so the UI needs no `.env`.
Backend on another port? `BACKEND_URL=http://localhost:9000 npm run dev`
