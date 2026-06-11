"""Mutable runtime configuration for the guardrails demo.

The demo lets a presenter tune behavior live without restarting the process:

  * Active filter profile (strict / standard / relaxed / custom)
  * Per-category severity thresholds
  * Custom blocklist terms
  * Toggle for the Azure Prompt Shields API call

Process-local. Resets on restart. Adequate for a single-pod demo.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from app.config import settings
from app.safety.filter_profiles import CATEGORIES, FilterProfile, get_profile

logger = logging.getLogger(__name__)


@dataclass
class RuntimeConfig:
    """Mutable runtime config governing demo pipeline behavior."""

    profile_name: str = "standard"
    custom_thresholds: Dict[str, int] = field(default_factory=dict)
    blocklist: List[str] = field(default_factory=list)
    prompt_shield_enabled: bool = True

    def to_dict(self) -> Dict[str, object]:
        return {
            "profile_name": self.profile_name,
            "custom_thresholds": dict(self.custom_thresholds),
            "blocklist": list(self.blocklist),
            "prompt_shield_enabled": self.prompt_shield_enabled,
            "categories": list(CATEGORIES),
        }

    def active_profile(self) -> FilterProfile:
        """Resolve the active FilterProfile, applying any custom thresholds."""
        if self.profile_name == "custom" or self.custom_thresholds:
            base_name = self.profile_name if self.profile_name != "custom" else "standard"
            base = get_profile(base_name)
            merged = dict(base.thresholds)
            merged.update({k: v for k, v in self.custom_thresholds.items() if k in CATEGORIES})
            display_name = "custom" if self.profile_name == "custom" else f"{self.profile_name}+custom"
            return FilterProfile(
                name=display_name,
                description="Runtime-customized thresholds",
                thresholds=merged,
            )
        return get_profile(self.profile_name)


_lock = threading.RLock()  # RLock allows same thread to acquire multiple times
_config = RuntimeConfig(prompt_shield_enabled=settings.enable_prompt_shields)


def get_config() -> RuntimeConfig:
    """Return a snapshot copy of the current runtime config."""
    with _lock:
        return RuntimeConfig(
            profile_name=_config.profile_name,
            custom_thresholds=dict(_config.custom_thresholds),
            blocklist=list(_config.blocklist),
            prompt_shield_enabled=_config.prompt_shield_enabled,
        )


def update_config(
    *,
    profile_name: Optional[str] = None,
    custom_thresholds: Optional[Dict[str, int]] = None,
    blocklist: Optional[List[str]] = None,
    prompt_shield_enabled: Optional[bool] = None,
) -> RuntimeConfig:
    """Apply partial updates to the runtime config."""
    with _lock:
        if profile_name is not None:
            if profile_name != "custom":
                get_profile(profile_name)  # validate
            _config.profile_name = profile_name
        if custom_thresholds is not None:
            cleaned: Dict[str, int] = {}
            for cat, sev in custom_thresholds.items():
                if cat not in CATEGORIES:
                    continue
                try:
                    sev_int = int(sev)
                except (TypeError, ValueError):
                    continue
                cleaned[cat] = max(0, min(6, sev_int))
            _config.custom_thresholds = cleaned
        if blocklist is not None:
            _config.blocklist = [t.strip() for t in blocklist if isinstance(t, str) and t.strip()]
        if prompt_shield_enabled is not None:
            _config.prompt_shield_enabled = bool(prompt_shield_enabled)
        logger.info("Runtime config updated: %s", asdict(_config))
        return RuntimeConfig(
            profile_name=_config.profile_name,
            custom_thresholds=dict(_config.custom_thresholds),
            blocklist=list(_config.blocklist),
            prompt_shield_enabled=_config.prompt_shield_enabled,
        )


def reset_config() -> RuntimeConfig:
    """Reset runtime config to defaults (mainly for tests)."""
    with _lock:
        _config.profile_name = "standard"
        _config.custom_thresholds = {}
        _config.blocklist = []
        _config.prompt_shield_enabled = settings.enable_prompt_shields
        return get_config()
