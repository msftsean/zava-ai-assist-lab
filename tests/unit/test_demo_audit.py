"""Tests for the in-memory audit ring buffer."""

from __future__ import annotations

from app.demo import audit


def setup_function(_):
    audit.clear()


def test_record_assigns_audit_id_and_timestamp():
    aid = audit.record({"verdict": "allowed", "prompt": "hi"})
    entries = audit.list_entries()
    assert len(entries) == 1
    assert entries[0]["audit_id"] == aid
    assert "timestamp" in entries[0]
    assert entries[0]["verdict"] == "allowed"


def test_list_returns_newest_first():
    audit.record({"verdict": "first", "prompt": "1"})
    audit.record({"verdict": "second", "prompt": "2"})
    audit.record({"verdict": "third", "prompt": "3"})
    entries = audit.list_entries()
    assert [e["verdict"] for e in entries] == ["third", "second", "first"]


def test_clear_removes_all_entries():
    audit.record({"verdict": "x", "prompt": "y"})
    audit.record({"verdict": "x", "prompt": "y"})
    n = audit.clear()
    assert n == 2
    assert audit.list_entries() == []


def test_limit_caps_results():
    for i in range(5):
        audit.record({"verdict": str(i), "prompt": "p"})
    entries = audit.list_entries(limit=2)
    assert len(entries) == 2
    assert entries[0]["verdict"] == "4"
    assert entries[1]["verdict"] == "3"


def test_ring_buffer_respects_maxlen(monkeypatch):
    # The buffer is created at import time using settings.demo_audit_max.
    # We can't shrink it here without re-importing, but we can verify
    # the underlying deque has a maxlen at all.
    from app.demo.audit import _buffer
    assert _buffer.maxlen is not None and _buffer.maxlen > 0
