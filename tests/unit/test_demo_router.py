"""Tests for the demo FastAPI router (/demo/*)."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.demo import audit, runtime_config
from app.main import app
from app.safety.content_filter import SafetyResult
from app.safety.prompt_shield import ShieldResult


def setup_function(_):
    audit.clear()
    runtime_config.reset_config()


def test_root_redirects_to_demo():
    client = TestClient(app, follow_redirects=False)
    r = client.get("/")
    assert r.status_code in (307, 308)
    assert r.headers["location"] == "/demo/"


def test_demo_index_serves_html():
    client = TestClient(app)
    r = client.get("/demo/")
    assert r.status_code == 200
    assert "Guardrails Console" in r.text


def test_scenarios_endpoint():
    client = TestClient(app)
    r = client.get("/demo/scenarios")
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()["scenarios"]]
    assert {"valid_public_safety", "malicious_explicit", "edge_case_report", "prompt_injection"}.issubset(set(ids))


def test_profiles_endpoint():
    client = TestClient(app)
    r = client.get("/demo/profiles")
    assert r.status_code == 200
    body = r.json()
    names = [p["name"] for p in body["profiles"]]
    assert {"strict", "standard", "relaxed"}.issubset(set(names))
    assert set(body["categories"]) == {"Hate", "SelfHarm", "Sexual", "Violence"}


def test_config_get_post_round_trip():
    client = TestClient(app)
    r = client.post(
        "/demo/config",
        json={
            "profile_name": "relaxed",
            "blocklist": ["foo", "bar"],
            "prompt_shield_enabled": False,
            "custom_thresholds": {"Hate": 5},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["profile_name"] == "relaxed"
    assert body["blocklist"] == ["foo", "bar"]
    assert body["prompt_shield_enabled"] is False
    assert body["custom_thresholds"]["Hate"] == 5

    r2 = client.get("/demo/config")
    assert r2.json()["profile_name"] == "relaxed"


def test_config_invalid_profile_returns_400():
    client = TestClient(app)
    r = client.post("/demo/config", json={"profile_name": "no-such-profile"})
    assert r.status_code == 400


def test_chat_happy_path():
    client = TestClient(app)
    with patch("app.demo.pipeline.scan", return_value=ShieldResult(False, [], "none", 0)), \
         patch("app.demo.pipeline.check_input_safety", return_value=SafetyResult(True, {"Hate": 0}, [])), \
         patch("app.demo.pipeline.check_output_safety", return_value=SafetyResult(True, {"Hate": 0}, [])), \
         patch("app.demo.pipeline._get_openai_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value.choices = [
            type("X", (), {"message": type("M", (), {"content": "fine"})()})
        ]
        r = client.post("/demo/chat", json={"prompt": "hi"})

    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "allowed"
    assert body["output"] == "fine"
    assert body["audit_id"]


def test_audit_endpoints():
    client = TestClient(app)
    audit.record({"verdict": "allowed", "prompt": "hi"})
    r = client.get("/demo/audit")
    assert r.status_code == 200
    assert len(r.json()["entries"]) == 1

    r = client.delete("/demo/audit")
    assert r.status_code == 200
    assert r.json()["cleared"] == 1
    assert client.get("/demo/audit").json()["entries"] == []
