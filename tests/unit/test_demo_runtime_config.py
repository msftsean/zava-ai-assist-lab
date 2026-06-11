"""Tests for the runtime config singleton used by the guardrails demo."""

from __future__ import annotations

from app.demo import runtime_config


def setup_function(_):
    runtime_config.reset_config()


def test_default_config_uses_standard_profile():
    cfg = runtime_config.get_config()
    assert cfg.profile_name == "standard"
    assert cfg.custom_thresholds == {}
    assert cfg.blocklist == []


def test_update_changes_profile_and_blocklist():
    cfg = runtime_config.update_config(profile_name="strict", blocklist=["secret", "internal"])
    assert cfg.profile_name == "strict"
    assert cfg.blocklist == ["secret", "internal"]


def test_invalid_profile_raises():
    import pytest
    with pytest.raises(KeyError):
        runtime_config.update_config(profile_name="nonexistent")


def test_custom_thresholds_clamped_and_validated():
    cfg = runtime_config.update_config(
        custom_thresholds={"Hate": 9, "Sexual": -2, "Bogus": 3, "Violence": "4"}
    )
    # 9 clamped to 6, -2 clamped to 0, "Bogus" dropped, "4" coerced to int.
    assert cfg.custom_thresholds["Hate"] == 6
    assert cfg.custom_thresholds["Sexual"] == 0
    assert cfg.custom_thresholds["Violence"] == 4
    assert "Bogus" not in cfg.custom_thresholds


def test_active_profile_merges_custom_thresholds():
    runtime_config.update_config(
        profile_name="standard", custom_thresholds={"Hate": 0}
    )
    profile = runtime_config.get_config().active_profile()
    assert profile.thresholds["Hate"] == 0
    # Other categories keep the standard default of 2.
    assert profile.thresholds["Violence"] == 2


def test_blocklist_strips_and_filters_empty():
    cfg = runtime_config.update_config(blocklist=["  hello  ", "", "  ", "world"])
    assert cfg.blocklist == ["hello", "world"]
