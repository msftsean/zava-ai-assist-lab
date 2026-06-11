"""
Integration tests – Query (RAG) pipeline
==========================================
End-to-end tests for the retrieval-augmented generation flow:
  1. Embed the user question
  2. Retrieve relevant chunks from Azure AI Search (+ optional pgvector)
  3. Compose a grounded prompt
  4. Call Azure OpenAI for the answer
  5. Return structured ``RAGResponse`` with cited sources

Marked ``@pytest.mark.integration`` — skipped by default.

MSI Lab guidance
----------------
These tests use mocks by default.  To test against live services, set
``AI_ASSIST_LIVE_TESTS=1`` and provide valid Azure credentials.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.query.rag import rag_query, RAGResponse


pytestmark = pytest.mark.integration


# ═══════════════════════════════════════════════════════════════════════════
# Retrieval returns documents
# ═══════════════════════════════════════════════════════════════════════════


class TestRetrievalReturnsDocs:
    """Ensure the retrieval step returns documents from AI Search."""

    def test_retrieval_returns_docs(self, mock_openai, mock_search_client, mock_postgres):
        """AI Search results should be captured and forwarded."""
        # Simulate search returning two relevant chunks
        mock_search_client.search.return_value = iter([
            {
                "chunk_id": "sop-backup.md::chunk-0",
                "source": "sop-backup.md",
                "content": "Full backups are performed every Sunday at 02:00 UTC.",
            },
            {
                "chunk_id": "sop-backup.md::chunk-1",
                "source": "sop-backup.md",
                "content": "Incremental backups run nightly on weekdays.",
            },
        ])

        with patch("app.query.rag._get_openai_client", return_value=mock_openai), \
             patch("app.query.rag.SearchClient", return_value=mock_search_client), \
             patch("app.query.rag.psycopg2") as mock_pg:

            mock_pg.connect.return_value = mock_postgres[0]
            mock_postgres[1].fetchall.return_value = []

            response = rag_query("When are backups performed?", use_pgvector=False)

        assert isinstance(response, RAGResponse)
        assert response.search_results_count == 2
        assert "sop-backup.md" in response.sources


# ═══════════════════════════════════════════════════════════════════════════
# Full RAG query flow
# ═══════════════════════════════════════════════════════════════════════════


class TestRAGQueryFlow:
    """Exercise the complete retrieve → prompt → generate flow."""

    def test_rag_query_flow(self, mock_openai, mock_search_client, mock_postgres):
        """The full RAG pipeline should return an answer with sources."""
        # Provide search results
        mock_search_client.search.return_value = iter([
            {
                "chunk_id": "sop-incident.md::chunk-0",
                "source": "sop-incident.md",
                "content": "Identify and classify the incident severity.",
            },
        ])

        # Configure the LLM answer
        mock_choice = MagicMock()
        mock_choice.message.content = (
            "According to sop-incident.md, the first step is to identify "
            "and classify the incident severity."
        )
        mock_openai.chat.completions.create.return_value.choices = [mock_choice]

        with patch("app.query.rag._get_openai_client", return_value=mock_openai), \
             patch("app.query.rag.SearchClient", return_value=mock_search_client), \
             patch("app.query.rag.psycopg2") as mock_pg:

            mock_pg.connect.return_value = mock_postgres[0]
            mock_postgres[1].fetchall.return_value = []

            response = rag_query("What is the first step in incident response?", use_pgvector=False)

        assert response.answer != ""
        assert "sop-incident.md" in response.sources
        assert response.search_results_count >= 1

    def test_rag_query_with_pgvector(self, mock_openai, mock_search_client, mock_postgres):
        """When ``use_pgvector=True``, pgvector results should also be counted."""
        mock_search_client.search.return_value = iter([
            {"chunk_id": "c1", "source": "sop.md", "content": "content"},
        ])

        # Simulate pgvector returning 2 results
        mock_postgres[1].fetchall.return_value = [
            ("c1", "sop.md", "content 1", 0.95),
            ("c2", "sop.md", "content 2", 0.90),
        ]

        with patch("app.query.rag._get_openai_client", return_value=mock_openai), \
             patch("app.query.rag.SearchClient", return_value=mock_search_client), \
             patch("app.query.rag.psycopg2") as mock_pg:

            mock_pg.connect.return_value = mock_postgres[0]

            response = rag_query("test question", use_pgvector=True)

        assert response.pgvector_results_count == 2
