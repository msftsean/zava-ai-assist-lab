"""
Integration tests – FastAPI API endpoints
===========================================
Tests the REST API layer using FastAPI's ``TestClient`` (httpx-backed).

Exercises:
  • ``GET /health`` – liveness / readiness probe
  • ``POST /query`` – RAG query endpoint
  • ``POST /ingest`` – document ingestion endpoint

Marked ``@pytest.mark.integration`` — skipped by default.

MSI Lab guidance
----------------
The ``TestClient`` sends real HTTP requests to the in-process ASGI app,
giving you confidence that routing, serialisation, and error handling
work correctly without needing a running server.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.ingestion.ingest import DocumentChunk
from app.query.rag import RAGResponse
from app.safety.content_filter import SafetyResult


pytestmark = pytest.mark.integration


# ═══════════════════════════════════════════════════════════════════════════
# Health endpoint
# ═══════════════════════════════════════════════════════════════════════════


class TestHealthEndpoint:
    """Verify the ``/health`` liveness probe."""

    def test_health_endpoint(self, test_client):
        """GET /health should return 200 with status=healthy."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "cloud" in data


# ═══════════════════════════════════════════════════════════════════════════
# Query endpoint
# ═══════════════════════════════════════════════════════════════════════════


class TestQueryEndpoint:
    """Verify the ``POST /query`` RAG endpoint."""

    def test_query_endpoint(self, test_client):
        """A valid query should return a structured JSON response."""
        mock_rag_response = RAGResponse(
            answer="Backups are performed every Sunday.",
            sources=["sop-backup.md"],
            search_results_count=2,
            pgvector_results_count=1,
        )

        with patch("app.query.rag_query", return_value=mock_rag_response):
            response = test_client.post(
                "/query",
                json={"question": "When are backups performed?", "top_k": 3},
            )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert data["answer"] == "Backups are performed every Sunday."

    def test_query_endpoint_missing_question(self, test_client):
        """A request without a ``question`` field should return 422."""
        response = test_client.post("/query", json={})
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
# Ingest endpoint
# ═══════════════════════════════════════════════════════════════════════════


class TestIngestEndpoint:
    """Verify the ``POST /ingest`` document ingestion endpoint."""

    def test_ingest_endpoint(self, test_client):
        """A valid ingest request should return the chunk count."""
        mock_chunks = [
            DocumentChunk(
                chunk_id="sop.md::chunk-0",
                source_blob="sop.md",
                content="content",
                chunk_index=0,
                metadata={},
            ),
            DocumentChunk(
                chunk_id="sop.md::chunk-1",
                source_blob="sop.md",
                content="more content",
                chunk_index=1,
                metadata={},
            ),
        ]

        with patch("app.ingestion.ingest_documents", return_value=mock_chunks):
            response = test_client.post("/ingest", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["chunks_ingested"] == 2

    def test_ingest_endpoint_with_custom_params(self, test_client):
        """Custom chunk_size and overlap should be accepted."""
        with patch("app.ingestion.ingest_documents", return_value=[]) as mock_ingest:
            response = test_client.post(
                "/ingest",
                json={"container": "my-container", "chunk_size": 200, "overlap": 20},
            )

        assert response.status_code == 200
        # Verify custom params were forwarded
        mock_ingest.assert_called_once_with(
            container="my-container",
            chunk_size=200,
            overlap=20,
        )
