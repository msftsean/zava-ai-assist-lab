"""
Document Indexing Module
========================
Generates embeddings via Azure OpenAI, stores vectors in PostgreSQL
(pgvector), and indexes documents into Azure AI Search with vector fields.
"""

from __future__ import annotations

import logging
from typing import List

import psycopg2
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchFieldDataType as DT,
)

from app.config import settings
from app.ingestion.ingest import DocumentChunk

logger = logging.getLogger(__name__)

# ── Embedding helpers ────────────────────────────────────────────────────


def _get_openai_client() -> AzureOpenAI:
    """Create an AzureOpenAI client for embedding generation."""
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_base_url,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


def generate_embeddings(texts: List[str], batch_size: int = 16) -> List[List[float]]:
    """Generate embeddings for a list of texts using Azure OpenAI.

    Args:
        texts: The strings to embed.
        batch_size: Number of texts per API call (max varies by model).

    Returns:
        A list of embedding vectors (one per input text).
    """
    client = _get_openai_client()
    all_embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(
            input=batch,
            model=settings.azure_openai_embedding_deployment,
        )
        all_embeddings.extend([item.embedding for item in response.data])
        logger.info("Embedded batch %d–%d of %d", i, i + len(batch), len(texts))

    return all_embeddings


# ── pgvector storage ─────────────────────────────────────────────────────


def _ensure_pgvector_table(conn) -> None:
    """Create the embeddings table and pgvector extension if they don't exist."""
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS document_embeddings (
                chunk_id   TEXT PRIMARY KEY,
                source     TEXT,
                content    TEXT,
                embedding  vector(1536)
            );
            """
        )
    conn.commit()


def store_in_pgvector(chunks: List[DocumentChunk], embeddings: List[List[float]]) -> int:
    """Upsert document chunks and their embeddings into PostgreSQL.

    Args:
        chunks: Document chunks from the ingestion step.
        embeddings: Corresponding embedding vectors.

    Returns:
        Number of rows upserted.
    """
    conn = psycopg2.connect(settings.postgres_dsn)
    try:
        _ensure_pgvector_table(conn)
        with conn.cursor() as cur:
            for chunk, emb in zip(chunks, embeddings):
                cur.execute(
                    """
                    INSERT INTO document_embeddings (chunk_id, source, content, embedding)
                    VALUES (%s, %s, %s, %s::vector)
                    ON CONFLICT (chunk_id)
                    DO UPDATE SET content = EXCLUDED.content,
                                  embedding = EXCLUDED.embedding;
                    """,
                    (chunk.chunk_id, chunk.source_blob, chunk.content, str(emb)),
                )
        conn.commit()
        logger.info("Stored %d embeddings in pgvector", len(chunks))
        return len(chunks)
    finally:
        conn.close()


# ── Azure AI Search ──────────────────────────────────────────────────────


def create_search_index() -> None:
    """Create or update the Azure AI Search index with vector support."""
    credential = AzureKeyCredential(settings.azure_search_api_key)
    index_client = SearchIndexClient(
        endpoint=settings.azure_search_endpoint,
        credential=credential,
    )

    fields = [
        SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True, filterable=True),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="default-vector-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="default-hnsw")],
        profiles=[
            VectorSearchProfile(
                name="default-vector-profile",
                algorithm_configuration_name="default-hnsw",
            )
        ],
    )

    index = SearchIndex(
        name=settings.azure_search_index_name,
        fields=fields,
        vector_search=vector_search,
    )

    index_client.create_or_update_index(index)
    logger.info("Search index '%s' created / updated", settings.azure_search_index_name)


def index_in_search(
    chunks: List[DocumentChunk],
    embeddings: List[List[float]],
    batch_size: int = 100,
) -> int:
    """Upload document chunks to Azure AI Search.

    Args:
        chunks: Document chunks from the ingestion step.
        embeddings: Corresponding embedding vectors.
        batch_size: Documents per upload batch.

    Returns:
        Total number of documents indexed.
    """
    credential = AzureKeyCredential(settings.azure_search_api_key)
    search_client = SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index_name,
        credential=credential,
    )

    import re

    def _safe_key(key: str) -> str:
        """Replace characters not allowed in AI Search keys with dashes."""
        return re.sub(r"[^a-zA-Z0-9_=\-]", "-", key)

    documents = [
        {
            "chunk_id": _safe_key(chunk.chunk_id),
            "source": chunk.source_blob,
            "content": chunk.content,
            "embedding": emb,
        }
        for chunk, emb in zip(chunks, embeddings)
    ]

    total = 0
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        result = search_client.upload_documents(documents=batch)
        total += len(batch)
        logger.info("Indexed batch %d–%d", i, i + len(batch))

    return total


# ── Orchestrator ─────────────────────────────────────────────────────────


def index_documents(chunks: List[DocumentChunk]) -> dict:
    """Full indexing pipeline: embed → pgvector → AI Search.

    Args:
        chunks: Document chunks produced by the ingestion step.

    Returns:
        Summary dict with counts.
    """
    texts = [c.content for c in chunks]
    embeddings = generate_embeddings(texts)

    create_search_index()
    search_count = index_in_search(chunks, embeddings)
    pg_count = store_in_pgvector(chunks, embeddings)

    return {
        "chunks_processed": len(chunks),
        "indexed_in_search": search_count,
        "stored_in_pgvector": pg_count,
    }
