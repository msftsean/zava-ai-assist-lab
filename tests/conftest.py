"""
Pytest conftest – shared fixtures for AI Assist Lab tests.
==========================================================

Provides:
  • Environment variable overrides so tests never hit real Azure services.
  • Mock fixtures for Azure Blob Storage, OpenAI, AI Search, and Content Safety.
  • A FastAPI ``TestClient`` fixture wired to the application.
  • Sample document / chunk helpers for use in unit and integration tests.

MSI Lab note
------------
All external-service fixtures use ``unittest.mock`` by default.  When you are
ready to run against *live* Azure services, set the environment variable
``AI_ASSIST_LIVE_TESTS=1`` and provide valid credentials in your ``.env``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# 1. Environment variable overrides – applied before any app imports
# ---------------------------------------------------------------------------

# These env vars ensure the app's Settings object never requires real secrets
# during unit testing.  The autouse=True means they apply to every test.
TEST_ENV_VARS: Dict[str, str] = {
    "AZURE_CLOUD": "AzureUSGovernment",
    "AZURE_LOCATION": "usgovvirginia",
    "AZURE_OPENAI_ENDPOINT": "https://test-openai.openai.azure.us",
    "AZURE_OPENAI_API_KEY": "test-key-00000000",
    "AZURE_OPENAI_API_VERSION": "2024-02-15-preview",
    "AZURE_OPENAI_CHAT_DEPLOYMENT": "gpt-4o",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-3-small",
    "AZURE_SEARCH_ENDPOINT": "https://test-search.search.azure.us",
    "AZURE_SEARCH_API_KEY": "test-search-key",
    "AZURE_SEARCH_INDEX_NAME": "sop-index-test",
    "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=dGVzdA==;EndpointSuffix=core.usgovcloudapi.net",
    "AZURE_STORAGE_CONTAINER": "sop-documents-test",
    "AZURE_CONTENT_SAFETY_ENDPOINT": "https://test-safety.cognitiveservices.azure.us",
    "AZURE_CONTENT_SAFETY_API_KEY": "test-safety-key",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "ai_assist_test",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "postgres",
    "LOG_LEVEL": "DEBUG",
}


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    """Inject test-safe environment variables for every test."""
    for key, value in TEST_ENV_VARS.items():
        monkeypatch.setenv(key, value)


# ---------------------------------------------------------------------------
# 2. Mock Azure Blob Storage
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_blob_service():
    """Return a mock ``BlobServiceClient`` that yields controllable blobs.

    Usage in tests::

        def test_something(mock_blob_service):
            # The mock is already patched via ``mock_blob_service``
            blob_svc, container_client, blob_client = mock_blob_service
            blob_client.download_blob.return_value.readall.return_value = b"hello"
    """
    with patch("app.ingestion.ingest.BlobServiceClient") as MockBlobSvc:
        mock_svc_instance = MagicMock()
        MockBlobSvc.from_connection_string.return_value = mock_svc_instance

        mock_container_client = MagicMock()
        mock_svc_instance.get_container_client.return_value = mock_container_client

        mock_blob_client = MagicMock()
        mock_svc_instance.get_blob_client.return_value = mock_blob_client

        # Default: container lists nothing, blob downloads empty bytes
        mock_container_client.list_blobs.return_value = []
        mock_blob_client.download_blob.return_value.readall.return_value = b""

        yield mock_svc_instance, mock_container_client, mock_blob_client


# ---------------------------------------------------------------------------
# 3. Mock Azure OpenAI
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_openai():
    """Patch ``AzureOpenAI`` so no real API calls are made.

    Returns the mock client instance for assertion / configuration.
    """
    with patch("openai.AzureOpenAI") as MockOpenAI:
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client

        # Embedding default
        mock_embedding_response = MagicMock()
        mock_embedding_item = MagicMock()
        mock_embedding_item.embedding = [0.1] * 1536
        mock_embedding_response.data = [mock_embedding_item]
        mock_client.embeddings.create.return_value = mock_embedding_response

        # Chat completion default
        mock_chat_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "This is a test answer based on the SOP."
        mock_chat_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_chat_response

        yield mock_client


# ---------------------------------------------------------------------------
# 4. Mock Azure AI Search
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_search_client():
    """Patch ``SearchClient`` to return controllable search results."""
    with patch("azure.search.documents.SearchClient") as MockSearch:
        mock_client = MagicMock()
        MockSearch.return_value = mock_client

        # Default search results (empty)
        mock_client.search.return_value = iter([])
        mock_client.upload_documents.return_value = []

        yield mock_client


@pytest.fixture
def mock_search_index_client():
    """Patch ``SearchIndexClient`` for index creation tests."""
    with patch("azure.search.documents.indexes.SearchIndexClient") as MockIdx:
        mock_client = MagicMock()
        MockIdx.return_value = mock_client
        yield mock_client


# ---------------------------------------------------------------------------
# 5. Mock Azure Content Safety
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_content_safety():
    """Patch ``ContentSafetyClient`` with configurable analysis results.

    By default, all categories return severity 0 (safe).
    """
    with patch("app.safety.content_filter.ContentSafetyClient") as MockCS:
        mock_client = MagicMock()
        MockCS.return_value = mock_client

        # Build a default "all safe" response
        def _make_category(name: str, severity: int = 0):
            cat = MagicMock()
            cat.category.value = name
            cat.severity = severity
            return cat

        mock_response = MagicMock()
        mock_response.categories_analysis = [
            _make_category("Hate", 0),
            _make_category("Violence", 0),
            _make_category("SelfHarm", 0),
            _make_category("Sexual", 0),
        ]
        mock_client.analyze_text.return_value = mock_response

        # Expose helper so tests can reconfigure severities
        mock_client._make_category = _make_category
        mock_client._response = mock_response

        yield mock_client


# ---------------------------------------------------------------------------
# 6. FastAPI TestClient
# ---------------------------------------------------------------------------

@pytest.fixture
def test_client():
    """Create an ``httpx``-backed TestClient for the FastAPI app.

    This fixture imports ``app.main:app`` *after* the test-env vars are set
    so that ``Settings()`` picks up the test overrides.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        yield client


# ---------------------------------------------------------------------------
# 7. Sample documents & chunks
# ---------------------------------------------------------------------------

# A small SOP excerpt useful for testing chunking / search / RAG.
SAMPLE_SOP_TEXT = (
    "# System Backup and Recovery\n\n"
    "## Purpose\n"
    "This SOP defines the procedures for performing system backups and "
    "restoring data in the event of a failure.\n\n"
    "## Schedule\n"
    "Full backups are performed every Sunday at 02:00 UTC. Incremental "
    "backups run nightly at 02:00 UTC on all other days.\n\n"
    "## Procedure\n"
    "1. Verify disk space on the backup target.\n"
    "2. Initiate the backup job via the central management console.\n"
    "3. Validate backup integrity using checksums.\n"
    "4. Record the backup status in the operations log.\n"
)

SAMPLE_MARKDOWN_SOP = (
    "# Incident Response Procedures\n\n"
    "## Scope\n"
    "Applies to all production systems.\n\n"
    "## Steps\n"
    "1. Identify and classify the incident.\n"
    "2. Contain the affected systems.\n"
    "3. Eradicate the root cause.\n"
    "4. Recover normal operations.\n"
    "5. Conduct a post-incident review.\n"
)


@pytest.fixture
def sample_sop_text():
    """Return a sample SOP plain-text string."""
    return SAMPLE_SOP_TEXT


@pytest.fixture
def sample_markdown_sop():
    """Return a sample SOP in Markdown format."""
    return SAMPLE_MARKDOWN_SOP


@pytest.fixture
def sample_document_chunks():
    """Return a list of pre-built ``DocumentChunk`` objects for testing.

    Avoids importing from ``app.ingestion.ingest`` at module level so that
    the fixture works even before the ingestion module is fully wired up.
    """
    from app.ingestion.ingest import DocumentChunk

    return [
        DocumentChunk(
            chunk_id="sop-backup.md::chunk-0",
            source_blob="sop-backup.md",
            content="Full backups are performed every Sunday at 02:00 UTC.",
            chunk_index=0,
            metadata={"source": "sop-backup.md", "chunk_index": 0},
        ),
        DocumentChunk(
            chunk_id="sop-backup.md::chunk-1",
            source_blob="sop-backup.md",
            content="Incremental backups run nightly at 02:00 UTC.",
            chunk_index=1,
            metadata={"source": "sop-backup.md", "chunk_index": 1},
        ),
        DocumentChunk(
            chunk_id="sop-incident.md::chunk-0",
            source_blob="sop-incident.md",
            content="Identify and classify the incident. Contain affected systems.",
            chunk_index=0,
            metadata={"source": "sop-incident.md", "chunk_index": 0},
        ),
    ]


# ---------------------------------------------------------------------------
# 8. Mock PostgreSQL connection (for pgvector tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_postgres():
    """Patch ``psycopg2.connect`` to return a mock connection/cursor."""
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        # Default: SELECT returns no rows
        mock_cursor.fetchall.return_value = []

        yield mock_conn, mock_cursor
