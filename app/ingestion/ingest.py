"""
SOP Ingestion Module
====================
Connects to Azure Blob Storage, downloads SOP documents (.txt / .md),
chunks the content, and returns a list of document chunks with metadata
ready for embedding and indexing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from azure.storage.blob import BlobServiceClient

from app.config import settings
from app.utils.text_processing import chunk_text, clean_text

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """A single chunk of a source document."""

    chunk_id: str
    source_blob: str
    content: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


def _get_blob_service_client() -> BlobServiceClient:
    """Create a BlobServiceClient from the configured connection string."""
    return BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )


def list_blobs(container: str | None = None) -> List[str]:
    """List all blob names in the SOP container.

    Args:
        container: Override the default container name.

    Returns:
        A list of blob names (e.g. ``["sop-001.md", "sop-002.txt"]``).
    """
    container = container or settings.azure_storage_container
    client = _get_blob_service_client()
    container_client = client.get_container_client(container)
    return [blob.name for blob in container_client.list_blobs()]


def download_blob(blob_name: str, container: str | None = None) -> str:
    """Download a single blob and return its text content.

    Args:
        blob_name: Name of the blob to download.
        container: Override the default container name.

    Returns:
        The decoded text content of the blob.
    """
    container = container or settings.azure_storage_container
    client = _get_blob_service_client()
    blob_client = client.get_blob_client(container=container, blob=blob_name)
    data = blob_client.download_blob().readall()
    return data.decode("utf-8")


def _is_supported(blob_name: str) -> bool:
    """Return True if the blob has a supported text extension."""
    return blob_name.lower().endswith((".txt", ".md"))


def ingest_documents(
    container: str | None = None,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> List[DocumentChunk]:
    """End-to-end ingestion: list → download → clean → chunk.

    Args:
        container: Blob container name (default from settings).
        chunk_size: Characters per chunk (default from settings).
        overlap: Overlap between consecutive chunks (default from settings).

    Returns:
        A flat list of ``DocumentChunk`` objects across all blobs.
    """
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

    blob_names = list_blobs(container)
    logger.info("Found %d blobs in container '%s'", len(blob_names), container or settings.azure_storage_container)

    all_chunks: List[DocumentChunk] = []

    for blob_name in blob_names:
        if not _is_supported(blob_name):
            logger.debug("Skipping unsupported file: %s", blob_name)
            continue

        logger.info("Processing blob: %s", blob_name)
        raw_text = download_blob(blob_name, container)
        cleaned = clean_text(raw_text)
        text_chunks = chunk_text(cleaned, chunk_size=chunk_size, overlap=overlap)

        for idx, chunk in enumerate(text_chunks):
            all_chunks.append(
                DocumentChunk(
                    chunk_id=f"{blob_name}::chunk-{idx}",
                    source_blob=blob_name,
                    content=chunk,
                    chunk_index=idx,
                    metadata={"source": blob_name, "chunk_index": idx},
                )
            )

    logger.info("Ingested %d chunks from %d documents", len(all_chunks), len(blob_names))
    return all_chunks
