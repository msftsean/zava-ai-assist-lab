"""
Unit tests for app/query/rag.py
================================
Tests the RAG (Retrieval-Augmented Generation) pipeline components:

  • Prompt composition (context + question → messages)
  • Response structure (``RAGResponse`` dataclass)
  • Source attribution (cited sources propagated into response)

All Azure OpenAI and AI Search calls are mocked so the tests run
without any external services.

MSI Lab guidance
----------------
Understanding prompt composition is critical for RAG quality.
Experiment with modifying ``SYSTEM_PROMPT`` or the context format
in ``_build_prompt`` and observe how the model's behaviour changes.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.query.rag import (
    _build_prompt,
    rag_query,
    RAGResponse,
    SYSTEM_PROMPT,
)


# ═══════════════════════════════════════════════════════════════════════════
# Prompt composition
# ═══════════════════════════════════════════════════════════════════════════


class TestPromptComposition:
    """Verify that ``_build_prompt`` assembles context and question correctly."""

    def test_prompt_composition(self):
        """The composed prompt should include the question and context docs."""
        context_docs = [
            {"source": "sop-backup.md", "content": "Backups run every Sunday."},
            {"source": "sop-incident.md", "content": "Classify the incident first."},
        ]
        prompt = _build_prompt("When do backups run?", context_docs)

        # The prompt string should contain both pieces of context
        assert "Backups run every Sunday." in prompt
        assert "Classify the incident first." in prompt

        # The question should appear in the prompt
        assert "When do backups run?" in prompt

    def test_prompt_includes_source_labels(self):
        """Each context document's source should be labelled in the prompt."""
        context_docs = [
            {"source": "sop-backup.md", "content": "Backups run nightly."},
        ]
        prompt = _build_prompt("How often?", context_docs)

        assert "[Source: sop-backup.md]" in prompt

    def test_prompt_empty_context(self):
        """With no context docs, the prompt should still include the question."""
        prompt = _build_prompt("What is the policy?", [])

        assert "What is the policy?" in prompt

    def test_system_prompt_mentions_sops(self):
        """The system prompt should instruct the model to use only SOPs."""
        assert "SOP" in SYSTEM_PROMPT or "Standard Operating Procedures" in SYSTEM_PROMPT
        assert "context" in SYSTEM_PROMPT.lower()


# ═══════════════════════════════════════════════════════════════════════════
# Response structure
# ═══════════════════════════════════════════════════════════════════════════


class TestResponseStructure:
    """Verify the ``RAGResponse`` dataclass structure and defaults."""

    def test_response_structure(self):
        """A manually built RAGResponse should have all expected fields."""
        resp = RAGResponse(
            answer="Backups are scheduled for Sundays.",
            sources=["sop-backup.md"],
            search_results_count=3,
            pgvector_results_count=2,
        )
        assert resp.answer == "Backups are scheduled for Sundays."
        assert resp.sources == ["sop-backup.md"]
        assert resp.search_results_count == 3
        assert resp.pgvector_results_count == 2

    def test_response_defaults(self):
        """Default values for sources and counts should be sensible."""
        resp = RAGResponse(answer="test")
        assert resp.sources == []
        assert resp.search_results_count == 0
        assert resp.pgvector_results_count == 0


# ═══════════════════════════════════════════════════════════════════════════
# Source attribution (end-to-end with mocks)
# ═══════════════════════════════════════════════════════════════════════════


class TestSourceAttribution:
    """Verify that retrieved sources flow through to the final response."""

    def test_source_attribution(self, mock_openai, mock_search_client, mock_postgres):
        """Sources from AI Search should appear in the RAGResponse."""
        # Configure search to return two results
        mock_search_client.search.return_value = iter([
            {
                "chunk_id": "sop-backup.md::chunk-0",
                "source": "sop-backup.md",
                "content": "Full backups every Sunday.",
            },
            {
                "chunk_id": "sop-incident.md::chunk-0",
                "source": "sop-incident.md",
                "content": "Classify the incident severity.",
            },
        ])

        # Patch the clients at their usage sites
        with patch("app.query.rag._get_openai_client", return_value=mock_openai), \
             patch("app.query.rag.SearchClient", return_value=mock_search_client), \
             patch("app.query.rag.psycopg2") as mock_pg:

            mock_pg.connect.return_value = mock_postgres[0]
            mock_postgres[1].fetchall.return_value = []

            response = rag_query("When do backups run?", use_pgvector=False)

        assert isinstance(response, RAGResponse)
        assert "sop-backup.md" in response.sources
        assert response.search_results_count == 2

    def test_rag_query_calls_openai(self, mock_openai, mock_search_client, mock_postgres):
        """``rag_query`` should call the chat completion API."""
        mock_search_client.search.return_value = iter([
            {"chunk_id": "c1", "source": "sop.md", "content": "content"},
        ])

        with patch("app.query.rag._get_openai_client", return_value=mock_openai), \
             patch("app.query.rag.SearchClient", return_value=mock_search_client), \
             patch("app.query.rag.psycopg2") as mock_pg:

            mock_pg.connect.return_value = mock_postgres[0]
            mock_postgres[1].fetchall.return_value = []

            response = rag_query("test question", use_pgvector=False)

        # Chat completion should have been called once
        mock_openai.chat.completions.create.assert_called_once()
        assert response.answer != ""
