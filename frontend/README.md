# frontend/: one-page React + TypeScript UI

```
src/
├── App.tsx                         layout, health pills, selected collection
├── api/client.ts                   every backend call, typed
├── types.ts                        response types (mirror backend/app/*/schemas.py)
├── shared/
│   ├── StepTrace.tsx               pipeline trace, used by both panels
│   └── AnswerText.tsx              Markdown answer with clickable [n] citations
└── features/
    ├── collections/                collection picker (create / switch / delete)
    ├── ingestion/                  upload panel + document cards
    └── retrieval/                  chat panel + answer with sources
```

`vite.config.ts` forwards `/api/*` to `http://localhost:8000`, so the UI needs no `.env`.
Backend on another port? `BACKEND_URL=http://localhost:9000 npm run dev`

`npm run build` type-checks (strict TypeScript) and builds; `npm run typecheck` only checks.
