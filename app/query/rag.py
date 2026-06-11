"""
RAG Query Module
================
Implements the Retrieval-Augmented Generation pattern:
  1. Embed the user question
  2. Hybrid search (vector + keyword) in Azure AI Search
  3. Optional pgvector similarity search for comparison
  4. Compose a grounded prompt with retrieved context
  5. Call Azure OpenAI chat completion
  6. Return a structured response with cited sources
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import psycopg2
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an AI assistant that answers questions about Standard Operating "
    "Procedures (SOPs). Use ONLY the provided context to answer. If the context "
    "does not contain the answer, say so. Cite the source document for each fact."
)


@dataclass
class RAGResponse:
    """Structured response from a RAG query."""

    answer: str
    sources: List[str] = field(default_factory=list)
    search_results_count: int = 0
    pgvector_results_count: int = 0


def _get_openai_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_base_url,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


def _embed_query(text: str) -> List[float]:
    """Generate an embedding vector for the user query."""
    client = _get_openai_client()
    response = client.embeddings.create(
        input=[text],
        model=settings.azure_openai_embedding_deployment,
    )
    return response.data[0].embedding


# ── Azure AI Search (hybrid) ────────────────────────────────────────────


def _search_ai_search(query: str, embedding: List[float], top_k: int = 5) -> List[dict]:
    """Hybrid search: combines keyword relevance with vector similarity."""
    credential = AzureKeyCredential(settings.azure_search_api_key)
    client = SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index_name,
        credential=credential,
    )

    vector_query = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=top_k,
        fields="embedding",
    )

    results = client.search(
        search_text=query,
        vector_queries=[vector_query],
        top=top_k,
        select=["chunk_id", "source", "content"],
    )

    return [
        {"chunk_id": r["chunk_id"], "source": r["source"], "content": r["content"]}
        for r in results
    ]


# ── pgvector similarity search ──────────────────────────────────────────


def _search_pgvector(embedding: List[float], top_k: int = 5) -> List[dict]:
    """Cosine-similarity search against PostgreSQL pgvector."""
    conn = psycopg2.connect(settings.postgres_dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_id, source, content,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM document_embeddings
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
                """,
                (str(embedding), str(embedding), top_k),
            )
            rows = cur.fetchall()
        return [
            {"chunk_id": r[0], "source": r[1], "content": r[2], "similarity": float(r[3])}
            for r in rows
        ]
    finally:
        conn.close()


# ── Prompt composition ───────────────────────────────────────────────────


def _build_prompt(question: str, context_docs: List[dict]) -> str:
    """Assemble a context-grounded user message."""
    context_block = "\n\n---\n\n".join(
        f"[Source: {doc['source']}]\n{doc['content']}" for doc in context_docs
    )
    return (
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n\n"
        "Answer the question using only the context above. Cite sources."
    )


# ── Public API ───────────────────────────────────────────────────────────


def rag_query(
    question: str,
    top_k: int = 5,
    use_pgvector: bool = True,
) -> RAGResponse:
    """Execute a full RAG query.

    Args:
        question: The user's natural-language question.
        top_k: Number of context documents to retrieve.
        use_pgvector: Also query pgvector for comparison results.

    Returns:
        A ``RAGResponse`` with the answer and cited sources.
    """
    logger.info("RAG query: %s", question)

    # 1. Embed the question
    embedding = _embed_query(question)

    # 2. Retrieve from Azure AI Search (hybrid)
    search_results = _search_ai_search(question, embedding, top_k=top_k)
    logger.info("AI Search returned %d results", len(search_results))

    # 3. Optionally retrieve from pgvector
    pg_results: List[dict] = []
    if use_pgvector:
        try:
            pg_results = _search_pgvector(embedding, top_k=top_k)
            logger.info("pgvector returned %d results", len(pg_results))
        except Exception as exc:
            logger.warning("pgvector search failed: %s", exc)

    # 4. Compose prompt with AI Search results (primary)
    user_message = _build_prompt(question, search_results)

    # 5. Call Azure OpenAI
    client = _get_openai_client()
    completion = client.chat.completions.create(
        model=settings.azure_openai_chat_deployment,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    answer = completion.choices[0].message.content or ""
    sources = list({doc["source"] for doc in search_results})

    return RAGResponse(
        answer=answer,
        sources=sources,
        search_results_count=len(search_results),
        pgvector_results_count=len(pg_results),
    )
