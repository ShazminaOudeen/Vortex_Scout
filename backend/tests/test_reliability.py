"""Tests for Agent Reliability, Timeouts, Retries, and Circuit Breaker (Feature C5)."""
import time
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from google.genai import errors

from app.agent import gemini_client
from app.agent.gemini_client import (
    CircuitBreaker,
    _llm_briefing as _real_llm_briefing,
    _llm_structured_plan,
    build_checklist,
    generate_agent_plan,
    get_agent_health,
)
from app.models.anomaly import Anomaly, ChecklistAgentPlan


def _item(id_: str) -> Anomaly:
    return Anomaly(
        id=id_,
        sku_id=f"SKU-{id_}",
        sku_name=f"Product {id_}",
        aisle="02",
        bay="02A",
        category="Groceries",
        ledger_stock=15,
        hours_since_last_sale=4.0,
        p_void=0.85,
        detected_at=datetime.now(timezone.utc),
    )


def test_circuit_breaker_lifecycle():
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)
    assert cb.state == "closed"
    assert not cb.is_open()

    # 1 failure -> still closed
    cb.record_failure()
    assert cb.state == "closed"
    assert not cb.is_open()

    # 2 failures -> trips to open
    cb.record_failure()
    assert cb.state == "open"
    assert cb.is_open()

    # After cooldown -> transitions to half_open
    time.sleep(0.12)
    assert not cb.is_open()
    assert cb.state == "half_open"

    # Success restores closed state
    cb.record_success()
    assert cb.state == "closed"
    assert cb.consecutive_failures == 0


def test_circuit_breaker_bypasses_network_calls(monkeypatch):
    gemini_client._PLAN_CACHE.clear()
    gemini_client._CACHE.clear()
    gemini_client.CIRCUIT_BREAKER.reset()

    # Force open the circuit breaker
    gemini_client.CIRCUIT_BREAKER.record_failure()
    gemini_client.CIRCUIT_BREAKER.record_failure()
    gemini_client.CIRCUIT_BREAKER.record_failure()
    assert gemini_client.CIRCUIT_BREAKER.is_open()

    calls = []
    def boom(**kwargs):
        calls.append(1)
        raise RuntimeError("Should not be called when circuit breaker is open")

    monkeypatch.setattr(gemini_client, "genai", SimpleNamespace(Client=lambda **k: SimpleNamespace(models=SimpleNamespace(generate_content=boom))))
    monkeypatch.setattr(gemini_client, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="valid-mock-key",
        gemini_model="gemini-3.8-flash",
    ))

    items = [_item("cb_test")]
    cl = build_checklist(items)
    # Zero network calls made because breaker is open
    assert len(calls) == 0
    assert cl.briefing.startswith("Good morning!")
    assert len(cl.groups) == 1

    # Clean up
    gemini_client.CIRCUIT_BREAKER.reset()


def test_build_checklist_never_crashes_on_arbitrary_exceptions(monkeypatch):
    monkeypatch.setattr(gemini_client, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="valid-mock-key",
        gemini_model="gemini-3.8-flash",
    ))

    def disastrous_call(*args, **kwargs):
        raise errors.APIError("Fatal internal error", None)

    monkeypatch.setattr(gemini_client, "generate_agent_plan", disastrous_call)

    # Must safely fall back and never raise
    items = [_item("safe_1")]
    cl = build_checklist(items)
    assert cl is not None
    assert cl.briefing.startswith("Good morning!")
    assert cl.estimated_minutes >= 1


def test_retries_on_503_and_recovers(monkeypatch):
    gemini_client._CACHE.clear()
    gemini_client.CIRCUIT_BREAKER.reset()
    # conftest autouse fixture stubs _llm_briefing; restore real function for this unit test
    monkeypatch.setattr(gemini_client, "_llm_briefing", _real_llm_briefing)

    calls = {"count": 0}
    def flaky_llm(**kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            err = errors.APIError("Overloaded", None)
            err.code = 503
            raise err
        return SimpleNamespace(text="Scout recovered briefing.")

    client_mock = MagicMock()
    client_mock.models.generate_content = flaky_llm

    monkeypatch.setattr(gemini_client, "genai", SimpleNamespace(Client=lambda **k: client_mock))
    monkeypatch.setattr(gemini_client, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="mock-key",
        gemini_model="gemini-3.8-flash",
    ))
    monkeypatch.setattr(gemini_client, "time", SimpleNamespace(time=time.time, sleep=lambda s: None))

    items = [_item("retry_item")]
    res = gemini_client._llm_briefing(items)
    assert res == "Scout recovered briefing."
    assert calls["count"] == 2


def test_agent_health_endpoint(client):
    gemini_client.CIRCUIT_BREAKER.reset()
    resp = client.get("/api/v1/agent/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "circuit_breaker" in data
    assert data["circuit_breaker"]["state"] in ("closed", "open", "half_open")
    assert "cache" in data
    assert "timeout_ms" in data
