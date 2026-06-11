"""Document indexing and embedding package."""

from app.indexing.indexer import (
    generate_embeddings,
    store_in_pgvector,
    index_in_search,
    create_search_index,
    index_documents,
)

__all__ = [
    "generate_embeddings",
    "store_in_pgvector",
    "index_in_search",
    "create_search_index",
    "index_documents",
]
