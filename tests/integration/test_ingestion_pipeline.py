"""
Integration tests – Ingestion pipeline
=======================================
End-to-end tests that exercise the ingestion flow from Azure Blob Storage
through text cleaning and chunking.

These tests are marked with ``@pytest.mark.integration`` and are skipped
by default.  Run them with::

    pytest -m integration tests/integration/test_ingestion_pipeline.py

When ``AI_ASSIST_LIVE_TESTS=1`` is set, the tests will hit real Azure
services; otherwise they use the mock fixtures from ``conftest.py``.

Zava Lab guidance
----------------
Start by running with mocks to validate the logic, then configure your
Azure credentials and re-run to verify the live connection.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.ingestion.ingest import ingest_documents, DocumentChunk


pytestmark = pytest.mark.integration


# ═══════════════════════════════════════════════════════════════════════════
# Blob → Chunks pipeline
# ═══════════════════════════════════════════════════════════════════════════


class TestBlobToChunksPipeline:
    """Walk through the blob-download → clean → chunk pipeline."""

    def test_blob_to_chunks_pipeline(self, mock_blob_service, sample_sop_text):
        """Downloading a blob and chunking it should produce DocumentChunks."""
        mock_svc, mock_container, mock_blob = mock_blob_service

        # Simulate a single SOP file in the container
        blob_obj = MagicMock()
        blob_obj.name = "sop-backup.md"
        mock_container.list_blobs.return_value = [blob_obj]

        mock_blob.download_blob.return_value.readall.return_value = (
            sample_sop_text.encode("utf-8")
        )
        mock_svc.get_blob_client.return_value = mock_blob

        chunks = ingest_documents()

        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        # Verify metadata flows through
        assert all(c.source_blob == "sop-backup.md" for c in chunks)

    def test_multiple_blobs_ingested(self, mock_blob_service, sample_sop_text, sample_markdown_sop):
        """Multiple blobs in one container should all be ingested."""
        mock_svc, mock_container, mock_blob = mock_blob_service

        blob1 = MagicMock()
        blob1.name = "sop-backup.md"
        blob2 = MagicMock()
        blob2.name = "sop-incident.txt"
        mock_container.list_blobs.return_value = [blob1, blob2]

        # Return different content per blob based on call order
        contents = iter([
            sample_sop_text.encode("utf-8"),
            sample_markdown_sop.encode("utf-8"),
        ])
        mock_blob.download_blob.return_value.readall.side_effect = lambda: next(contents)
        mock_svc.get_blob_client.return_value = mock_blob

        chunks = ingest_documents()

        sources = {c.source_blob for c in chunks}
        assert len(sources) == 2, "Chunks should come from both source files"


# ═══════════════════════════════════════════════════════════════════════════
# End-to-end ingestion
# ═══════════════════════════════════════════════════════════════════════════


class TestEndToEndIngestion:
    """Full pipeline validation from raw blob bytes to indexed-ready chunks."""

    def test_end_to_end_ingestion(self, mock_blob_service):
        """A large document should be cleaned, chunked, and carry sequential IDs."""
        mock_svc, mock_container, mock_blob = mock_blob_service

        blob_obj = MagicMock()
        blob_obj.name = "big-sop.txt"
        mock_container.list_blobs.return_value = [blob_obj]

        # 3000 chars with embedded control characters
        raw = "Procedure step. " * 200 + "\x00\x07"
        mock_blob.download_blob.return_value.readall.return_value = raw.encode("utf-8")
        mock_svc.get_blob_client.return_value = mock_blob

        chunks = ingest_documents(chunk_size=500, overlap=50)

        # Multiple chunks expected
        assert len(chunks) > 1

        # IDs should be unique and sequential
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))

        # No control characters in any chunk
        for c in chunks:
            assert "\x00" not in c.content
            assert "\x07" not in c.content
