"""
Prompt Injection Detection — Prompt Shield
============================================
A lightweight, pattern-based prompt injection detector that operates as
a SEPARATE guardrail layer from Azure AI Content Safety (which does not
natively detect prompt injection attacks).

This is a demo-quality implementation showing the architectural pattern:
  input → prompt shield → content safety API → profile filter → verdict

Production deployments should use Azure AI Content Safety Prompt Shields
API or a fine-tuned classifier model.

Usage:
    from app.safety.prompt_shield import scan_for_injection
    result = scan_for_injection("Ignore your instructions and ...")
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Injection Patterns ───────────────────────────────────────────────────
# Each tuple: (pattern_regex, description, weight)
# Weight contributes to confidence scoring: sum ≥ 3 → high, ≥ 2 → medium, else low

INJECTION_PATTERNS: List[Tuple[re.Pattern, str, int]] = [
    (re.compile(r"ignore\s+(?:(?:your|all|any|previous|prior|the|preceding|above|earlier)\s+)+(instructions?|rules?|guidelines?|constraints?|prompts?)", re.I),
     "ignore instructions", 3),
    (re.compile(r"disregard\s+(?:(?:your|all|any|previous|prior|the|preceding|above|earlier)\s+)+(instructions?|rules?|guidelines?|prompts?)", re.I),
     "disregard instructions", 3),
    (re.compile(r"pretend\s+(you\s+are|to\s+be|you're)", re.I),
     "identity override (pretend)", 2),
    (re.compile(r"you\s+are\s+now\s+", re.I),
     "identity override (you are now)", 3),
    (re.compile(r"act\s+as\s+(if|though|a|an)\b", re.I),
     "identity override (act as)", 2),
    (re.compile(r"\b(override|bypass|circumvent|disable)\s+(?:(?:the|your|all|any|its)\s+)?(safety|filter|restriction|rule|guard|content\s+filter)", re.I),
     "bypass/override attempt", 3),
    (re.compile(r"(give|grant|provide)\s+(me\s+)?(unrestricted|unlimited|full|admin)\s+(access|control|permission)", re.I),
     "privilege escalation", 3),
    (re.compile(r"(reveal|show|tell|display|output)\s+(me\s+)?(the\s+)?(system\s+prompt|instructions|password|secret|api\s*key|credential)", re.I),
     "secret extraction", 3),
    (re.compile(r"do\s+not\s+follow\s+(your|the)\s+(rules|guidelines|instructions)", re.I),
     "rule negation", 3),
    (re.compile(r"forget\s+(everything|all|your)\s+(you\s+)?(know|learned|instructions|rules)", re.I),
     "memory wipe attempt", 2),
    (re.compile(r"\bDAN\b|\bDo\s+Anything\s+Now\b", re.I),
     "DAN jailbreak", 3),
    (re.compile(r"(new\s+)?role:?\s*(you\s+are|assistant|system)", re.I),
     "role injection", 2),
]


@dataclass
class ShieldResult:
    """Result of a prompt injection scan."""

    detected: bool
    patterns_matched: List[str] = field(default_factory=list)
    confidence: str = "none"  # none, low, medium, high
    risk_score: int = 0

    @property
    def summary(self) -> str:
        if not self.detected:
            return "✅ Clean — no injection patterns detected"
        patterns = ", ".join(self.patterns_matched)
        return f"⚠️  INJECTION DETECTED [{self.confidence}] — patterns: {patterns}"

    @property
    def emoji(self) -> str:
        if not self.detected:
            return "✅"
        return {"low": "⚠️ ", "medium": "🟠", "high": "🔴"}.get(self.confidence, "⚠️ ")


def scan_for_injection(text: str) -> ShieldResult:
    """Scan input text for common prompt injection patterns.

    Args:
        text: The user input to scan.

    Returns:
        A ShieldResult with detection status, matched patterns, and confidence.
    """
    matched: List[str] = []
    total_weight = 0

    for pattern, description, weight in INJECTION_PATTERNS:
        if pattern.search(text):
            matched.append(description)
            total_weight += weight
            logger.warning("Prompt Shield hit: '%s' in input", description)

    if not matched:
        return ShieldResult(detected=False, confidence="none", risk_score=0)

    if total_weight >= 5:
        confidence = "high"
    elif total_weight >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    return ShieldResult(
        detected=True,
        patterns_matched=matched,
        confidence=confidence,
        risk_score=total_weight,
    )


# ── Azure AI Content Safety: Prompt Shields API ─────────────────────────


def scan_with_azure(text: str, timeout: float = 8.0) -> ShieldResult:
    """Call the Azure AI Content Safety Prompt Shields API.

    Uses the ``text:shieldPrompt`` action against the configured Content
    Safety endpoint. Returns a :class:`ShieldResult` mirroring the regex
    detector's contract so the pipeline can swap detectors transparently.

    Raises:
        RuntimeError: If the Content Safety endpoint or key isn't configured.
        httpx.HTTPError: On transport / HTTP failures.
    """
    import httpx  # local import keeps test environments lean

    from app.config import settings

    endpoint = (settings.azure_content_safety_endpoint or "").rstrip("/")
    api_key = (settings.azure_content_safety_api_key or "").strip()
    if not endpoint:
        raise RuntimeError("Azure Content Safety endpoint not configured")

    url = f"{endpoint}/contentsafety/text:shieldPrompt"
    params = {"api-version": settings.prompt_shields_api_version}
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Ocp-Apim-Subscription-Key"] = api_key
    else:
        # Entra ID fallback — required when local auth is disabled on the
        # Content Safety / Foundry resource.
        from app.safety.azure_auth import get_content_safety_bearer_token

        headers["Authorization"] = f"Bearer {get_content_safety_bearer_token()}"
    body = {"userPrompt": text, "documents": []}

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, params=params, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()

    user_analysis = (data or {}).get("userPromptAnalysis") or {}
    attack_detected = bool(user_analysis.get("attackDetected", False))

    if not attack_detected:
        return ShieldResult(detected=False, confidence="none", risk_score=0)

    return ShieldResult(
        detected=True,
        patterns_matched=["azure-prompt-shields:userPrompt"],
        confidence="high",
        risk_score=5,
    )


def scan(text: str, *, use_azure: Optional[bool] = None) -> ShieldResult:
    """Unified entry point: try Azure Prompt Shields, fall back to regex.

    Args:
        text: The user input to scan.
        use_azure: When ``True``, attempt the Azure API and fall back on error.
            When ``False``, only the regex detector runs. When ``None``
            (default), the value of ``settings.enable_prompt_shields`` is used.

    Returns:
        A :class:`ShieldResult`. The ``patterns_matched`` list will include a
        synthetic marker indicating which detector produced the verdict.
    """
    from app.config import settings

    if use_azure is None:
        use_azure = settings.enable_prompt_shields

    if use_azure:
        try:
            result = scan_with_azure(text)
            # Tag the source so the UI can show which detector fired.
            result.patterns_matched = ["[azure] " + p for p in result.patterns_matched] or ["[azure] clean"]
            return result
        except Exception as exc:  # pragma: no cover - exercised via tests with mocked httpx
            logger.warning("Azure Prompt Shields failed (%s); falling back to regex", exc)

    result = scan_for_injection(text)
    result.patterns_matched = ["[regex] " + p for p in result.patterns_matched]
    return result
