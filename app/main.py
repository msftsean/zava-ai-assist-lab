"""
FastAPI Application – AI Assist RAG Service
============================================
Provides REST endpoints for SOP ingestion, indexing, RAG queries,
and content-safety checks.

Run locally::

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import settings
from app.demo import router as demo_router
from app.demo.router import STATIC_DIR as DEMO_STATIC_DIR

# ── Logging setup ────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Startup safety checks ────────────────────────────────────────────────
# Warn if Content Safety is not configured (unless in test environment)
if not os.getenv("PYTEST_CURRENT_TEST"):
    if not settings.azure_content_safety_endpoint:
        logger.warning(
            "⚠️  AZURE_CONTENT_SAFETY_ENDPOINT is not set. The /demo endpoints "
            "will fail when Content Safety is called. Add it to your .env."
        )
    elif not settings.azure_content_safety_api_key:
        logger.info(
            "ℹ️  AZURE_CONTENT_SAFETY_API_KEY is empty — using DefaultAzureCredential "
            "(Entra ID) for Content Safety. Ensure 'az login' is active and you have the "
            "'Cognitive Services User' role on the resource."
        )

# ── FastAPI app ──────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Assist – SOP RAG Service",
    description="Retrieval-Augmented Generation over Standard Operating Procedures",
    version="0.1.0",
)

app.include_router(demo_router)
app.mount("/demo/static", StaticFiles(directory=str(DEMO_STATIC_DIR)), name="demo-static")


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect the bare root URL to the guardrails demo for easy access."""
    return RedirectResponse(url="/demo/")


# ── Request / Response models ────────────────────────────────────────────


class IngestRequest(BaseModel):
    container: Optional[str] = None
    chunk_size: Optional[int] = None
    overlap: Optional[int] = None


class IngestResponse(BaseModel):
    chunks_ingested: int


class IndexResponse(BaseModel):
    chunks_processed: int
    indexed_in_search: int
    stored_in_pgvector: int


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    use_pgvector: bool = True


class QueryResponse(BaseModel):
    answer: str
    sources: list
    search_results_count: int
    pgvector_results_count: int


class SafetyRequest(BaseModel):
    text: str
    thresholds: Optional[Dict[str, int]] = None


class SafetyResponse(BaseModel):
    is_safe: bool
    details: Dict[str, int]
    blocked_categories: list


# ── Endpoints ────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    """Liveness / readiness probe."""
    return {"status": "healthy", "cloud": settings.azure_cloud}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    """Ingest SOP documents from Azure Blob Storage."""
    try:
        from app.ingestion import ingest_documents

        chunks = ingest_documents(
            container=request.container,
            chunk_size=request.chunk_size,
            overlap=request.overlap,
        )
        # Store chunks in app state for subsequent /index call
        app.state.last_ingested_chunks = chunks
        return IngestResponse(chunks_ingested=len(chunks))
    except Exception as exc:
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/index", response_model=IndexResponse)
async def index():
    """Index previously ingested documents (embed → pgvector → AI Search)."""
    try:
        from app.indexing import index_documents

        chunks = getattr(app.state, "last_ingested_chunks", None)
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No ingested chunks found. Call /ingest first.",
            )

        result = index_documents(chunks)
        return IndexResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Indexing failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Answer a question using the RAG pipeline."""
    try:
        from app.query import rag_query

        response = rag_query(
            question=request.question,
            top_k=request.top_k,
            use_pgvector=request.use_pgvector,
        )
        return QueryResponse(
            answer=response.answer,
            sources=response.sources,
            search_results_count=response.search_results_count,
            pgvector_results_count=response.pgvector_results_count,
        )
    except Exception as exc:
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/safety/check", response_model=SafetyResponse)
async def safety_check(request: SafetyRequest):
    """Run a content-safety analysis on arbitrary text."""
    try:
        from app.safety import check_input_safety

        result = check_input_safety(request.text, thresholds=request.thresholds)
        return SafetyResponse(
            is_safe=result.is_safe,
            details=result.details,
            blocked_categories=result.blocked_categories,
        )
    except Exception as exc:
        logger.exception("Safety check failed")
        raise HTTPException(status_code=500, detail=str(exc))
