"""
Text Processing Utilities
=========================
Helpers for chunking, token counting, and text cleanup used throughout
the ingestion and query pipelines.
"""

from __future__ import annotations

import re
from typing import List

import tiktoken


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split *text* into overlapping chunks of roughly *chunk_size* characters.

    Args:
        text: The input string to split.
        chunk_size: Maximum number of characters per chunk.
        overlap: Number of characters shared between consecutive chunks.

    Returns:
        A list of text chunks. Empty input returns an empty list.
    """
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count the number of tokens in *text* for the given model.

    Args:
        text: Input text.
        model: OpenAI model name used to select the tokenizer.

    Returns:
        Token count as an integer.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def clean_text(text: str) -> str:
    """Normalize whitespace and strip control characters.

    Args:
        text: Raw text input.

    Returns:
        Cleaned string with collapsed whitespace and no leading/trailing space.
    """
    # Remove null bytes and other control characters (keep newlines / tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Collapse runs of whitespace into a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
