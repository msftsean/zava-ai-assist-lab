"""
Integration tests – Content Safety pipeline
=============================================
Tests the Azure AI Content Safety integration end-to-end with mocks.

Verifies:
  • Safe content flows through the pre-check without blocking
  • Harmful content is blocked before reaching the model
  • Both input and output safety checks work consistently

Marked ``@pytest.mark.integration`` — skipped by default.

Zava Lab guidance
----------------
Azure Content Safety returns severity 0–6 for four categories.
The default threshold of 2 means anything ≥ 2 is blocked.
These tests demonstrate how the threshold mechanism works.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from app.safety.content_filter import (
    check_input_safety,
    check_output_safety,
    SafetyResult,
)


pytestmark = pytest.mark.integration


def _build_mock_response(severities: dict):
    """Helper to build a mock Content Safety response."""
    items = []
    for name, severity in severities.items():
        item = MagicMock()
        item.category.value = name
        item.severity = severity
        items.append(item)
    response = MagicMock()
    response.categories_analysis = items
    return response


# ═══════════════════════════════════════════════════════════════════════════
# Content safety flow
# ═══════════════════════════════════════════════════════════════════════════


class TestContentSafetyFlow:
    """End-to-end safety check with all-safe severities."""

    def test_content_safety_flow(self, mock_content_safety):
        """A benign question should pass both input and output checks."""
        # Input check
        input_result = check_input_safety("What is the backup schedule?")
        assert input_result.is_safe is True
        assert input_result.blocked_categories == []

        # Simulate model output
        output_result = check_output_safety(
            "Backups are performed every Sunday at 02:00 UTC."
        )
        assert output_result.is_safe is True

    def test_details_populated(self, mock_content_safety):
        """The ``details`` dict should contain severity scores for all categories."""
        result = check_input_safety("Normal text for analysis")

        assert isinstance(result.details, dict)
        assert len(result.details) == 4  # Hate, Violence, SelfHarm, Sexual


# ═══════════════════════════════════════════════════════════════════════════
# Harmful content blocked
# ═══════════════════════════════════════════════════════════════════════════


class TestSafetyBlocksHarmfulContent:
    """Verify that high-severity content is blocked before reaching the model."""

    def test_safety_blocks_harmful_content(self, mock_content_safety):
        """Content with a Violence severity of 5 should be blocked."""
        harmful_response = _build_mock_response(
            {"Hate": 0, "Violence": 5, "SelfHarm": 0, "Sexual": 0}
        )
        mock_content_safety.analyze_text.return_value = harmful_response

        result = check_input_safety("some harmful input")

        assert result.is_safe is False
        assert "Violence" in result.blocked_categories

    def test_output_safety_also_blocks(self, mock_content_safety):
        """The output check should block harmful model-generated text too."""
        harmful_response = _build_mock_response(
            {"Hate": 4, "Violence": 0, "SelfHarm": 0, "Sexual": 0}
        )
        mock_content_safety.analyze_text.return_value = harmful_response

        result = check_output_safety("model generated something hateful")

        assert result.is_safe is False
        assert "Hate" in result.blocked_categories

    def test_custom_thresholds_in_integration(self, mock_content_safety):
        """Custom thresholds should override defaults in the full flow."""
        borderline = _build_mock_response(
            {"Hate": 0, "Violence": 3, "SelfHarm": 0, "Sexual": 0}
        )
        mock_content_safety.analyze_text.return_value = borderline

        # Strict (default=2) → blocked
        strict = check_input_safety("test")
        assert strict.is_safe is False

        # Lenient (threshold=5) → allowed
        lenient = check_input_safety(
            "test",
            thresholds={"Hate": 5, "Violence": 5, "SelfHarm": 5, "Sexual": 5},
        )
        assert lenient.is_safe is True
