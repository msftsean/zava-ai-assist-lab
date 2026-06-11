"""
Customizable Content Filter Profiles
=====================================
Application-layer filtering that sits ON TOP of Azure AI Content Safety API
severity scores. These profiles are SEPARATE from Azure Foundry-level content
filters — they let the application owner tune thresholds per deployment context.

Three built-in profiles:
  • strict   — Enterprise/government: block at severity ≥ 1
  • standard — Normal business use: block at severity ≥ 2 (matches existing default)
  • relaxed  — Internal/dev use: block only at severity ≥ 4

Usage:
    from app.safety.filter_profiles import get_profile, apply_profile
    profile = get_profile("strict")
    result = apply_profile(profile, severity_scores)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

CATEGORIES = ["Hate", "SelfHarm", "Sexual", "Violence"]


@dataclass
class FilterProfile:
    """A named configuration of per-category severity thresholds."""

    name: str
    description: str
    thresholds: Dict[str, int]

    def threshold_for(self, category: str) -> int:
        return self.thresholds.get(category, self.thresholds.get("default", 2))


@dataclass
class FilterResult:
    """Structured result from applying a profile to severity scores."""

    profile_name: str
    allowed: bool
    triggered_categories: List[Dict[str, int]] = field(default_factory=list)
    category_details: Dict[str, Dict[str, int]] = field(default_factory=dict)

    @property
    def summary(self) -> str:
        if self.allowed:
            return f"✅ Allowed by {self.profile_name}"
        triggers = ", ".join(
            f"{t['category']} (sev {t['severity']} ≥ {t['threshold']})"
            for t in self.triggered_categories
        )
        return f"❌ Blocked by {self.profile_name}: {triggers}"


# ── Built-in Profiles ────────────────────────────────────────────────────

PROFILES: Dict[str, FilterProfile] = {
    "strict": FilterProfile(
        name="strict",
        description="Enterprise/government — blocks at severity ≥ 1 across all categories",
        thresholds={cat: 1 for cat in CATEGORIES},
    ),
    "standard": FilterProfile(
        name="standard",
        description="Normal business use — blocks at severity ≥ 2 (current default)",
        thresholds={cat: 2 for cat in CATEGORIES},
    ),
    "relaxed": FilterProfile(
        name="relaxed",
        description="Internal/dev use — blocks only extreme content at severity ≥ 4",
        thresholds={cat: 4 for cat in CATEGORIES},
    ),
}


def get_profile(name: str) -> FilterProfile:
    """Retrieve a filter profile by name.

    Raises:
        KeyError: If the profile name is not found.
    """
    if name not in PROFILES:
        available = ", ".join(PROFILES.keys())
        raise KeyError(f"Unknown profile '{name}'. Available: {available}")
    return PROFILES[name]


def list_profiles() -> List[FilterProfile]:
    """Return all registered filter profiles."""
    return list(PROFILES.values())


def register_profile(profile: FilterProfile) -> None:
    """Register a custom filter profile at runtime."""
    PROFILES[profile.name] = profile
    logger.info("Registered custom filter profile: %s", profile.name)


def apply_profile(
    profile: FilterProfile,
    severity_scores: Dict[str, int],
) -> FilterResult:
    """Apply a filter profile to a set of Azure Content Safety severity scores.

    Args:
        profile: The filter profile to apply.
        severity_scores: Dict mapping category names to severity ints (0-6).

    Returns:
        A FilterResult indicating whether the content is allowed.
    """
    triggered: List[Dict[str, int]] = []
    details: Dict[str, Dict[str, int]] = {}

    for category in CATEGORIES:
        severity = severity_scores.get(category, 0)
        threshold = profile.threshold_for(category)
        details[category] = {"severity": severity, "threshold": threshold}

        if severity >= threshold:
            triggered.append(
                {"category": category, "severity": severity, "threshold": threshold}
            )
            logger.info(
                "Profile %s triggered — %s: severity %d ≥ threshold %d",
                profile.name,
                category,
                severity,
                threshold,
            )

    return FilterResult(
        profile_name=profile.name,
        allowed=len(triggered) == 0,
        triggered_categories=triggered,
        category_details=details,
    )


def evaluate_all_profiles(
    severity_scores: Dict[str, int],
) -> Dict[str, FilterResult]:
    """Run severity scores through ALL registered profiles.

    Returns a dict mapping profile name → FilterResult.
    """
    return {
        name: apply_profile(profile, severity_scores)
        for name, profile in PROFILES.items()
    }
