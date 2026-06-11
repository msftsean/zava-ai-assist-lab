"""
Unit tests for app/ingestion/ingest.py
=======================================
Tests the SOP document ingestion pipeline with mocked Azure Blob Storage.

Covered functionality:
  • Parsing plain-text files
  • Parsing Markdown files (title extraction, cleaning)
  • Chunking parsed documents into ``DocumentChunk`` objects
  • Metadata propagation through the pipeline

All Azure Blob Storage interactions are mocked via the ``mock_blob_service``
fixture defined in ``conftest.py``.

Zava Lab guidance
----------------
Try modifying ``chunk_size`` and ``overlap`` to observe how chunk counts
and content change — this is key to understanding RAG retrieval quality.
"""

import pytest
from unittest.mock import MagicMock

from app.ingestion.ingest import (
    DocumentChunk,
    list_blobs,
    download_blob,
    ingest_documents,
)
from app.utils.text_processing import chunk_text, clean_text


# ═══════════════════════════════════════════════════════════════════════════
# Parse text file
# ═══════════════════════════════════════════════════════════════════════════


class TestParseTextFile:
    """Verify plain-text file handling through the ingestion pipeline."""

    def test_parse_text_file(self, mock_blob_service):
        """A .txt blob should be downloaded, cleaned, and chunked."""
        mock_svc, mock_container, mock_blob = mock_blob_service

        # Simulate one .txt blob in the container
        blob_obj = MagicMock()
        blob_obj.name = "procedures.txt"
        mock_container.list_blobs.return_value = [blob_obj]

        # The blob content
        content = "Step 1: Power on the system.\nStep 2: Verify all indicators."
        mock_blob.download_blob.return_value.readall.return_value = content.encode("utf-8")
        mock_svc.get_blob_client.return_value = mock_blob

        chunks = ingest_documents()

        # Should produce at least one chunk
        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert chunks[0].source_blob == "procedures.txt"

    def test_text_content_is_cleaned(self, mock_blob_service):
        """Control characters and excess whitespace should be removed."""
        mock_svc, mock_container, mock_blob = mock_blob_service

        blob_obj = MagicMock()
        blob_obj.name = "dirty.txt"
        mock_container.list_blobs.return_value = [blob_obj]

        dirty = "Hello\x00World\x07   extra   spaces"
        mock_blob.download_blob.return_value.readall.return_value = dirty.encode("utf-8")
        mock_svc.get_blob_client.return_value = mock_blob

        chunks = ingest_documents()
        combined = " ".join(c.content for c in chunks)

        assert "\x00" not in combined
        assert "\x07" not in combined


# ═══════════════════════════════════════════════════════════════════════════
# Parse Markdown file
# ═══════════════════════════════════════════════════════════════════════════


class TestParseMarkdownFile:
    """Verify Markdown file handling (the most common SOP format)."""

    def test_parse_markdown_file(self, mock_blob_service, sample_markdown_sop):
        """A .md blob should be ingested and produce DocumentChunks."""
        mock_svc, mock_container, mock_blob = mock_blob_service

        blob_obj = MagicMock()
        blob_obj.name = "sop-incident.md"
        mock_container.list_blobs.return_value = [blob_obj]
        mock_blob.download_blob.return_value.readall.return_value = (
            sample_markdown_sop.encode("utf-8")
        )
        mock_svc.get_blob_client.return_value = mock_blob

        chunks = ingest_documents()

        assert len(chunks) >= 1
        assert chunks[0].source_blob == "sop-incident.md"

    def test_unsupported_file_skipped(self, mock_blob_service):
        """Files that are not .txt or .md should be silently skipped."""
        mock_svc, mock_container, _ = mock_blob_service

        blob_obj = MagicMock()
        blob_obj.name = "image.png"
        mock_container.list_blobs.return_value = [blob_obj]

        chunks = ingest_documents()
        assert chunks == []


# ═══════════════════════════════════════════════════════════════════════════
# Chunk documents
# ═══════════════════════════════════════════════════════════════════════════


class TestChunkDocuments:
    """Verify that large documents are correctly split into chunks."""

    def test_chunk_documents(self, mock_blob_service):
        """A document larger than ``chunk_size`` should be split."""
        mock_svc, mock_container, mock_blob = mock_blob_service

        blob_obj = MagicMock()
        blob_obj.name = "long-doc.txt"
        mock_container.list_blobs.return_value = [blob_obj]

        # 2000-char document with default chunk_size=500
        long_text = "A" * 2000
        mock_blob.download_blob.return_value.readall.return_value = long_text.encode("utf-8")
        mock_svc.get_blob_client.return_value = mock_blob

        chunks = ingest_documents(chunk_size=500, overlap=50)

        assert len(chunks) > 1, "Long document should produce multiple chunks"

    def test_chunk_ids_are_unique(self, mock_blob_service):
        """Each chunk should have a unique ``chunk_id``."""
        mock_svc, mock_container, mock_blob = mock_blob_service

        blob_obj = MagicMock()
        blob_obj.name = "multi-chunk.txt"
        mock_container.list_blobs.return_value = [blob_obj]
        mock_blob.download_blob.return_value.readall.return_value = ("word " * 500).encode("utf-8")
        mock_svc.get_blob_client.return_value = mock_blob

        chunks = ingest_documents()
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids)), "Chunk IDs must be unique"


# ═══════════════════════════════════════════════════════════════════════════
# Document metadata
# ═══════════════════════════════════════════════════════════════════════════


class TestDocumentMetadata:
    """Verify that metadata is correctly attached to each chunk."""

    def test_document_metadata(self, mock_blob_service):
        """Every chunk should carry ``source`` and ``chunk_index`` metadata."""
        mock_svc, mock_container, mock_blob = mock_blob_service

        blob_obj = MagicMock()
        blob_obj.name = "sop-checklist.md"
        mock_container.list_blobs.return_value = [blob_obj]
        mock_blob.download_blob.return_value.readall.return_value = (
            ("Checklist item. " * 200).encode("utf-8")
        )
        mock_svc.get_blob_client.return_value = mock_blob

        chunks = ingest_documents()

        for chunk in chunks:
            assert "source" in chunk.metadata
            assert "chunk_index" in chunk.metadata
            assert chunk.metadata["source"] == "sop-checklist.md"

    def test_chunk_index_is_sequential(self, mock_blob_service):
        """``chunk_index`` values should start at 0 and increase by 1."""
        mock_svc, mock_container, mock_blob = mock_blob_service

        blob_obj = MagicMock()
        blob_obj.name = "sequential.txt"
        mock_container.list_blobs.return_value = [blob_obj]
        mock_blob.download_blob.return_value.readall.return_value = ("X" * 2000).encode("utf-8")
        mock_svc.get_blob_client.return_value = mock_blob

        chunks = ingest_documents()
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))
