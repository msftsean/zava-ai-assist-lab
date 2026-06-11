"""
Unit tests for app/safety/content_filter.py
============================================
Tests content-safety analysis using mocked Azure AI Content Safety responses.

The tests verify:
  • Safe content passes through without being blocked
  • Unsafe content (high severity) is correctly flagged
  • Custom threshold configuration is honoured
  • The ``SafetyResult`` dataclass has the expected structure

All Azure Content Safety API calls are mocked — no network required.

MSI Lab guidance
----------------
In production, Azure Content Safety returns severity scores 0–6 for four
categories: Hate, Violence, SelfHarm, Sexual.  The default threshold is 2,
meaning any category ≥ 2 triggers a block.  Adjust thresholds based on
your organisation's acceptable-use policy.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.safety.content_filter import (
    check_input_safety,
    check_output_safety,
    SafetyResult,
    DEFAULT_THRESHOLDS,
    _analyze,
)


# ── Helpers ──────────────────────────────────────────────────────────────

def _build_mock_response(severities: dict):
    """Build a mock ``analyze_text`` response with the given severity map.

    Args:
        severities: e.g. ``{"Hate": 0, "Violence": 4, "SelfHarm": 0, "Sexual": 0}``
    """
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
# Safe content
# ═══════════════════════════════════════════════════════════════════════════


class TestSafeContentPasses:
    """Content with all-zero severities should pass the safety check."""

    def test_safe_content_passes(self, mock_content_safety):
        """A completely benign input should return ``is_safe=True``."""
        result = check_input_safety("What is the backup schedule?")

        assert isinstance(result, SafetyResult)
        assert result.is_safe is True
        assert result.blocked_categories == []

    def test_safe_output_passes(self, mock_content_safety):
        """Model-generated safe output should also pass."""
        result = check_output_safety("Backups are performed every Sunday at 02:00 UTC.")

        assert result.is_safe is True


# ═══════════════════════════════════════════════════════════════════════════
# Unsafe content
# ═══════════════════════════════════════════════════════════════════════════


class TestUnsafeContentFails:
    """Content exceeding severity thresholds should be blocked."""

    def test_unsafe_content_fails(self, mock_content_safety):
        """When Violence severity is high, the result should be unsafe."""
        # Reconfigure the mock response to return high violence
        unsafe_response = _build_mock_response(
            {"Hate": 0, "Violence": 4, "SelfHarm": 0, "Sexual": 0}
        )
        mock_content_safety.analyze_text.return_value = unsafe_response

        result = check_input_safety("some violent text")

        assert result.is_safe is False
        assert "Violence" in result.blocked_categories

    def test_multiple_categories_blocked(self, mock_content_safety):
        """Multiple categories above threshold should all appear in blocked list."""
        unsafe_response = _build_mock_response(
            {"Hate": 3, "Violence": 5, "SelfHarm": 0, "Sexual": 4}
        )
        mock_content_safety.analyze_text.return_value = unsafe_response

        result = check_input_safety("very problematic input")

        assert result.is_safe is False
        assert "Hate" in result.blocked_categories
        assert "Violence" in result.blocked_categories
        assert "Sexual" in result.blocked_categories
        assert "SelfHarm" not in result.blocked_categories


# ═══════════════════════════════════════════════════════════════════════════
# Threshold configuration
# ═══════════════════════════════════════════════════════════════════════════


class TestThresholdConfiguration:
    """Verify that custom thresholds change blocking behaviour."""

    def test_threshold_configuration(self, mock_content_safety):
        """Raising the threshold should allow previously-blocked content."""
        # Response with Violence severity = 3
        borderline = _build_mock_response(
            {"Hate": 0, "Violence": 3, "SelfHarm": 0, "Sexual": 0}
        )
        mock_content_safety.analyze_text.return_value = borderline

        # Default threshold (2) → should block
        result_strict = check_input_safety("test text")
        assert result_strict.is_safe is False

        # Lenient threshold (5) → should pass
        lenient = {"Hate": 5, "Violence": 5, "SelfHarm": 5, "Sexual": 5}
        result_lenient = check_input_safety("test text", thresholds=lenient)
        assert result_lenient.is_safe is True

    def test_default_thresholds_are_2(self):
        """All four default thresholds should be 2."""
        for category in ("Hate", "Violence", "SelfHarm", "Sexual"):
            assert DEFAULT_THRESHOLDS[category] == 2


# ═══════════════════════════════════════════════════════════════════════════
# SafetyResult structure
# ═══════════════════════════════════════════════════════════════════════════


class TestSafetyResultStructure:
    """Ensure the SafetyResult dataclass has the expected fields."""

    def test_safety_result_structure(self):
        """Manually constructed SafetyResult should have correct fields."""
        result = SafetyResult(
            is_safe=True,
            details={"Hate": 0, "Violence": 0, "SelfHarm": 0, "Sexual": 0},
            blocked_categories=[],
        )
        assert hasattr(result, "is_safe")
        assert hasattr(result, "details")
        assert hasattr(result, "blocked_categories")

    def test_safety_result_defaults(self):
        """Default ``details`` and ``blocked_categories`` should be empty."""
        result = SafetyResult(is_safe=True)
        assert result.details == {}
        assert result.blocked_categories == []
