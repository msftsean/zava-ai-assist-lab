"""
Content Safety Module
=====================
Pre- and post-checks using Azure AI Content Safety to ensure that both
user input and model responses comply with configurable safety thresholds.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory

from app.config import settings
from app.safety.azure_auth import get_content_safety_credential

logger = logging.getLogger(__name__)

# Default severity thresholds (0 = safest, 6 = most permissive).
# Any category score at or above its threshold triggers a block.
DEFAULT_THRESHOLDS: Dict[str, int] = {
    "Hate": 2,
    "Violence": 2,
    "SelfHarm": 2,
    "Sexual": 2,
}


@dataclass
class SafetyResult:
    """Outcome of a content-safety analysis."""

    is_safe: bool
    details: Dict[str, int] = field(default_factory=dict)
    blocked_categories: list = field(default_factory=list)


def _get_client() -> ContentSafetyClient:
    """Instantiate the Azure AI Content Safety client.

    Uses an API key when ``AZURE_CONTENT_SAFETY_API_KEY`` is set; otherwise
    falls back to ``DefaultAzureCredential`` (Entra ID / managed identity /
    az CLI). This supports environments where local-auth is disabled by
    tenant policy (common on Azure AI Foundry resources).
    """
    return ContentSafetyClient(
        endpoint=settings.azure_content_safety_endpoint,
        credential=get_content_safety_credential(),
    )


def _analyze(
    text: str,
    thresholds: Optional[Dict[str, int]] = None,
    blocklist_terms: Optional[list] = None,
) -> SafetyResult:
    """Run text through Azure AI Content Safety and compare to thresholds.

    Args:
        text: The text to analyze.
        thresholds: Per-category severity thresholds. Defaults to
                    ``DEFAULT_THRESHOLDS``.
        blocklist_terms: Optional case-insensitive terms that, if present in
                    ``text``, force a block via a synthetic ``Blocklist``
                    category (severity = 6).

    Returns:
        A ``SafetyResult`` indicating whether the text is safe.
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS
    client = _get_client()

    request = AnalyzeTextOptions(text=text)
    response = client.analyze_text(request)

    details: Dict[str, int] = {}
    blocked: list = []

    for item in response.categories_analysis:
        category_name = item.category.value if hasattr(item.category, "value") else str(item.category)
        severity = item.severity
        details[category_name] = severity

        threshold = thresholds.get(category_name, 2)
        if severity >= threshold:
            blocked.append(category_name)
            logger.warning(
                "Content blocked — category=%s severity=%d threshold=%d",
                category_name,
                severity,
                threshold,
            )

    if blocklist_terms:
        text_lower = text.lower()
        hits = [t for t in blocklist_terms if t and t.lower() in text_lower]
        if hits:
            details["Blocklist"] = 6
            blocked.append("Blocklist")
            logger.warning("Content blocked by custom blocklist — terms=%s", hits)
        else:
            details.setdefault("Blocklist", 0)

    is_safe = len(blocked) == 0
    return SafetyResult(is_safe=is_safe, details=details, blocked_categories=blocked)


def check_input_safety(
    text: str,
    thresholds: Optional[Dict[str, int]] = None,
    blocklist_terms: Optional[list] = None,
) -> SafetyResult:
    """Pre-check: analyze user input *before* sending it to the model.

    Args:
        text: User-supplied text.
        thresholds: Optional custom thresholds.
        blocklist_terms: Optional case-insensitive blocklist terms.

    Returns:
        ``SafetyResult`` with pass/fail.
    """
    logger.info("Running input safety check (%d chars)", len(text))
    return _analyze(text, thresholds, blocklist_terms)


def check_output_safety(
    text: str,
    thresholds: Optional[Dict[str, int]] = None,
    blocklist_terms: Optional[list] = None,
) -> SafetyResult:
    """Post-check: analyze model output *before* returning it to the user.

    Args:
        text: Model-generated text.
        thresholds: Optional custom thresholds.
        blocklist_terms: Optional case-insensitive blocklist terms.

    Returns:
        ``SafetyResult`` with pass/fail.
    """
    logger.info("Running output safety check (%d chars)", len(text))
    return _analyze(text, thresholds, blocklist_terms)
