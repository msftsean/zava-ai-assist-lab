"""
Unit tests for app/utils/text_processing.py
============================================
Tests the three core text-processing utilities used throughout the
ingestion and query pipelines:

  • ``chunk_text``   – split text into overlapping windows
  • ``count_tokens`` – approximate / tiktoken-based token counting
  • ``clean_text``   – whitespace normalisation and control-char removal

These tests run without any external services or mocks.

MSI Lab guidance
----------------
After completing the lab, try adding edge-case tests (e.g., Unicode text,
very large documents, chunk_size == 1) to deepen your understanding.
"""

import pytest

from app.utils.text_processing import chunk_text, count_tokens, clean_text


# ═══════════════════════════════════════════════════════════════════════════
# chunk_text
# ═══════════════════════════════════════════════════════════════════════════


class TestChunkTextBasic:
    """Verify basic chunking behaviour with no overlap."""

    def test_chunk_text_basic(self):
        """A long string should be split into chunks of the specified size."""
        # Create a deterministic string of 100 characters
        text = "A" * 100

        # Chunk into pieces of 30 characters, no overlap
        chunks = chunk_text(text, chunk_size=30, overlap=0)

        # We expect ceil(100/30) = 4 chunks  (30 + 30 + 30 + 10)
        assert len(chunks) == 4
        assert chunks[0] == "A" * 30
        assert chunks[-1] == "A" * 10  # last chunk is smaller

    def test_chunk_text_preserves_all_content(self):
        """Concatenating all chunks (no overlap) should reconstruct the text."""
        text = "The quick brown fox jumps over the lazy dog. " * 5
        chunks = chunk_text(text, chunk_size=50, overlap=0)

        reconstructed = "".join(chunks)
        assert reconstructed == text


class TestChunkTextWithOverlap:
    """Verify overlapping chunking behaviour."""

    def test_chunk_text_with_overlap(self):
        """Chunks should share ``overlap`` characters with their neighbour."""
        text = "0123456789" * 10  # 100 chars: 0123456789 repeated
        chunks = chunk_text(text, chunk_size=30, overlap=10)

        # With chunk_size=30 and overlap=10, step = 30 - 10 = 20
        # Expected number of chunks: ceil(100/20) = 5
        assert len(chunks) >= 4

        # The end of chunk 0 should appear at the start of chunk 1
        overlap_from_first = chunks[0][-10:]
        start_of_second = chunks[1][:10]
        assert overlap_from_first == start_of_second, (
            "Overlap region must be identical between adjacent chunks"
        )

    def test_overlap_greater_than_zero_produces_more_chunks(self):
        """Using overlap should produce more chunks than without."""
        text = "word " * 200  # 1 000 characters
        no_overlap = chunk_text(text, chunk_size=100, overlap=0)
        with_overlap = chunk_text(text, chunk_size=100, overlap=25)

        assert len(with_overlap) > len(no_overlap)


class TestChunkTextEmptyInput:
    """Edge case: empty or whitespace-only strings."""

    def test_chunk_text_empty_input(self):
        """An empty string should return an empty list."""
        assert chunk_text("") == []

    def test_chunk_text_none_input(self):
        """None should return an empty list (falsy value)."""
        assert chunk_text(None) == []  # type: ignore[arg-type]


class TestChunkTextSmallInput:
    """Edge case: input smaller than chunk_size."""

    def test_chunk_text_small_input(self):
        """Text shorter than chunk_size returns a single chunk."""
        short = "Hello, world!"
        chunks = chunk_text(short, chunk_size=500)

        assert len(chunks) == 1
        assert chunks[0] == short

    def test_chunk_text_exact_chunk_size(self):
        """Text exactly equal to chunk_size returns one chunk (no overlap)."""
        text = "X" * 500
        chunks = chunk_text(text, chunk_size=500, overlap=0)

        assert len(chunks) == 1
        assert chunks[0] == text


# ═══════════════════════════════════════════════════════════════════════════
# count_tokens
# ═══════════════════════════════════════════════════════════════════════════


class TestCountTokens:
    """Verify token counting with tiktoken."""

    def test_count_tokens(self):
        """A simple sentence should produce a positive token count."""
        tokens = count_tokens("Hello, how are you?")
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_count_tokens_empty(self):
        """Empty text should have zero tokens."""
        assert count_tokens("") == 0

    def test_count_tokens_model_fallback(self):
        """An unknown model name should fall back gracefully."""
        # The function uses tiktoken.encoding_for_model with a KeyError fallback
        tokens = count_tokens("test", model="nonexistent-model-xyz")
        assert tokens > 0

    def test_count_tokens_scales_with_length(self):
        """Longer text should have proportionally more tokens."""
        short = count_tokens("Hello")
        long = count_tokens("Hello " * 100)
        assert long > short


# ═══════════════════════════════════════════════════════════════════════════
# clean_text
# ═══════════════════════════════════════════════════════════════════════════


class TestCleanText:
    """Verify text cleaning / normalisation."""

    def test_clean_text_collapses_whitespace(self):
        """Multiple spaces / tabs should be collapsed to a single space."""
        result = clean_text("hello    world\t\ttabs")
        assert "  " not in result
        assert "\t" not in result

    def test_clean_text_strips_control_chars(self):
        """Null bytes and control characters should be removed."""
        dirty = "hello\x00world\x07end"
        result = clean_text(dirty)
        assert "\x00" not in result
        assert "\x07" not in result
        assert "helloworld" in result.replace(" ", "")

    def test_clean_text_trims(self):
        """Leading and trailing whitespace should be removed."""
        result = clean_text("   padded   ")
        assert result == "padded"

    def test_clean_text_preserves_newlines(self):
        """Newlines should be preserved (not collapsed to spaces)."""
        result = clean_text("line1\nline2\n\nline3")
        # The function keeps newlines but collapses 3+ into 2
        assert "\n" in result

    def test_clean_text_empty(self):
        """Empty input should return an empty string."""
        assert clean_text("") == ""
