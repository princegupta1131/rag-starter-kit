"""
App entry point: one FastAPI server hosting both services.

    ingestion_service  -> /api/documents/*   (content in)
    retrieval_service  -> /api/chat          (answers out)
    /api/health        -> is the DB reachable and the key set?

Run:  uvicorn app.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ingestion_service.api import router as ingestion_router
from app.retrieval_service.api import router as retrieval_router
from app.shared.database import get_conn, init_schema, recover_interrupted_jobs


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_schema()
    recover_interrupted_jobs()
    yield


app = FastAPI(title="RAG Starter Kit", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ingestion_router)
app.include_router(retrieval_router)


@app.get("/api/health")
def health():
    try:
        with get_conn() as conn:
            docs, chunks = conn.execute(
                "SELECT (SELECT count(*) FROM documents WHERE status = 'ready'), (SELECT count(*) FROM chunks)"
            ).fetchone()
        database = "ok"
    except Exception as e:
        database, docs, chunks = f"error: {e}", 0, 0
    return {
        "database": database,
        "gemini_key": "set" if settings.gemini_api_key else "missing",
        "chat_model": settings.chat_model,
        "embed_model": f"{settings.embed_model} ({settings.embed_dim} dims)",
        "ready_documents": docs,
        "chunks": chunks,
    }
