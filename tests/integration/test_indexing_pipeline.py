"""
Integration tests – Indexing pipeline
======================================
Tests the embedding generation, search-index creation, and vector storage
steps that transform ingested document chunks into searchable vectors.

Marked ``@pytest.mark.integration`` — skipped by default.

MSI Lab guidance
----------------
These tests validate that the indexing module correctly:
  1. Calls Azure OpenAI to generate 1536-dimensional embedding vectors
  2. Creates / updates the Azure AI Search index schema
  3. Stores chunks + embeddings in both AI Search and pgvector
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.ingestion.ingest import DocumentChunk


pytestmark = pytest.mark.integration


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_chunks(n: int = 3) -> list:
    """Create *n* test DocumentChunks."""
    return [
        DocumentChunk(
            chunk_id=f"test-doc.md::chunk-{i}",
            source_blob="test-doc.md",
            content=f"Test content for chunk number {i}. " * 10,
            chunk_index=i,
            metadata={"source": "test-doc.md", "chunk_index": i},
        )
        for i in range(n)
    ]


# ═══════════════════════════════════════════════════════════════════════════
# Embedding generation
# ═══════════════════════════════════════════════════════════════════════════


class TestEmbeddingGeneration:
    """Verify that embeddings are generated for all input texts."""

    def test_embedding_generation(self, mock_openai):
        """``generate_embeddings`` should return one vector per input text."""
        with patch("app.indexing.indexer._get_openai_client", return_value=mock_openai):
            from app.indexing.indexer import generate_embeddings

            texts = ["chunk one", "chunk two", "chunk three"]

            # Configure mock to return 3 embeddings
            items = [MagicMock(embedding=[0.1] * 1536) for _ in texts]
            mock_openai.embeddings.create.return_value.data = items

            embeddings = generate_embeddings(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 1536 for e in embeddings)


# ═══════════════════════════════════════════════════════════════════════════
# Search index creation
# ═══════════════════════════════════════════════════════════════════════════


class TestSearchIndexCreation:
    """Verify that ``create_search_index`` calls the Azure SDK correctly."""

    def test_search_index_creation(self, mock_search_index_client):
        """The index client's ``create_or_update_index`` should be called."""
        with patch(
            "app.indexing.indexer.SearchIndexClient",
            return_value=mock_search_index_client,
        ), patch("app.indexing.indexer.AzureKeyCredential"):
            from app.indexing.indexer import create_search_index

            create_search_index()

        mock_search_index_client.create_or_update_index.assert_called_once()

        # Inspect the index that was passed to the SDK
        call_args = mock_search_index_client.create_or_update_index.call_args
        index = call_args[0][0] if call_args[0] else call_args[1].get("index")
        assert index is not None


# ═══════════════════════════════════════════════════════════════════════════
# Vector storage (pgvector + AI Search)
# ═══════════════════════════════════════════════════════════════════════════


class TestVectorStorage:
    """Verify that chunks and embeddings are stored in both backends."""

    def test_vector_storage(self, mock_openai, mock_search_client, mock_postgres):
        """``index_documents`` should embed, store in pgvector, and index in search."""
        chunks = _make_chunks(3)

        # 3 embedding vectors
        items = [MagicMock(embedding=[0.1] * 1536) for _ in chunks]
        mock_openai.embeddings.create.return_value.data = items

        with patch("app.indexing.indexer._get_openai_client", return_value=mock_openai), \
             patch("app.indexing.indexer.SearchClient", return_value=mock_search_client), \
             patch("app.indexing.indexer.SearchIndexClient", return_value=MagicMock()), \
             patch("app.indexing.indexer.AzureKeyCredential"), \
             patch("app.indexing.indexer.psycopg2") as mock_pg:

            mock_pg.connect.return_value = mock_postgres[0]

            from app.indexing.indexer import index_documents

            result = index_documents(chunks)

        assert result["chunks_processed"] == 3
        assert result["indexed_in_search"] == 3
        assert result["stored_in_pgvector"] == 3
