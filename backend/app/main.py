"""
App entry point: one FastAPI server for all services.

    /api/collections   collections_service  (knowledge bases)
    /api/documents     ingestion_service    (content in)
    /api/chat          retrieval_service    (answers out)
    /api/health        is everything connected?

Run: make run   (or: uvicorn app.main:app --reload --port 8000). API docs at /docs.
"""
import logging
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.collections_service.api import router as collections_router
from app.config import settings
from app.core.database import close_pool, ensure_database, explain_db_error, get_conn, open_pool
from app.core.errors import register_error_handlers
from app.core.logging_setup import setup_logging
from app.core.migrations import run_migrations
from app.ingestion_service.api import router as ingestion_router
from app.providers import get_embedder
from app.repositories import documents as documents_repo
from app.retrieval_service.api import router as retrieval_router

log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    try:
        if ensure_database():
            log.info("created the database in DATABASE_URL")
        run_migrations()
    except psycopg.OperationalError as e:
        log.error("can't use DATABASE_URL: %s  (details: make check)", explain_db_error(e))
        raise SystemExit(1) from None
    open_pool()
    if interrupted := documents_repo.mark_interrupted():
        log.warning("%d document(s) were mid-ingestion at shutdown and are marked failed", interrupted)
    log.info("ready: provider=%s chat=%s embed=%s", settings.llm_provider, settings.chat_model, settings.embed_model)
    yield
    close_pool()


app = FastAPI(title="RAG Starter Kit", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)
app.include_router(collections_router)
app.include_router(ingestion_router)
app.include_router(retrieval_router)


class Health(BaseModel):
    database: str
    provider: str
    api_key: str
    chat_model: str
    embed_model: str
    ready_documents: int
    stale_documents: int
    chunks: int


@app.get("/api/health", response_model=Health, tags=["health"])
def health():
    counts = {"ready_documents": 0, "stale_documents": 0, "chunks": 0}
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")
        counts = documents_repo.counts(get_embedder().name)
        database = "ok"
    except Exception as e:
        database = f"error: {e}"
    return {
        "database": database,
        "provider": settings.llm_provider,
        "api_key": "set" if settings.api_key else "missing",
        "chat_model": settings.chat_model,
        "embed_model": f"{settings.embed_model} ({settings.embed_dim} dims)",
        **counts,
    }
