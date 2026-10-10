from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from google.genai import errors

from app.agent import gemini_client
from app.agent.gemini_client import (
    _group,
    _llm_briefing,
    _template_briefing,
    build_checklist,
    verify_gemini_connection,
)
from app.models.anomaly import Anomaly


def _make_anomaly(id_: str, aisle: str, bay: str, p_void: float = 0.85, ledger: int = 10, hours: float = 5.0) -> Anomaly:
    return Anomaly(
        id=id_,
        sku_id=f"SKU-{id_}",
        sku_name=f"Product {id_}",
        aisle=aisle,
        bay=bay,
        category="Groceries",
        p_void=p_void,
        ledger_stock=ledger,
        hours_since_last_sale=hours,
        detected_at=datetime.now(timezone.utc),
    )


def test_template_briefing_formats_correctly():
    assert _template_briefing([]) == "Good morning! No likely shelf voids right now."

    one = [_make_anomaly("1", "02", "02A")]
    assert "1 high-probability void detected in aisle 02" in _template_briefing(one)

    two_same_aisle = [_make_anomaly("1", "02", "02A"), _make_anomaly("2", "02", "02B")]
    assert "2 high-probability voids detected in aisle 02" in _template_briefing(two_same_aisle)

    two_diff_aisles = [_make_anomaly("1", "02", "02A"), _make_anomaly("2", "05", "05A")]
    assert "2 high-probability voids detected in aisles 02, 05" in _template_briefing(two_diff_aisles)


def test_group_organizes_and_sorts_correctly():
    items = [
        _make_anomaly("1", "05", "05B", p_void=0.7),
        _make_anomaly("2", "02", "02A", p_void=0.8),
        _make_anomaly("3", "02", "02A", p_void=0.9),
    ]
    groups = _group(items)
    assert len(groups) == 2
    assert groups[0].aisle == "02"
    assert groups[1].aisle == "05"
    # bay 02A should have item 3 (p_void 0.9) before item 2 (p_void 0.8)
    assert [i.id for i in groups[0].items] == ["3", "2"]


def test_build_checklist_falls_back_to_template_when_gemini_fails(monkeypatch):
    items = [_make_anomaly("1", "02", "02A")]
    monkeypatch.setattr(gemini_client, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="mock-key",
        gemini_model="mock-model",
    ))

    def fail_llm(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(gemini_client, "_llm_briefing", fail_llm)

    checklist = build_checklist(items)
    assert checklist.briefing.startswith("Good morning!")
    assert "1 high-probability void" in checklist.briefing
    assert checklist.estimated_minutes >= 1
    assert len(checklist.groups) == 1


def test_llm_briefing_caches_result(monkeypatch):
    gemini_client._CACHE.clear()
    items = [_make_anomaly("c1", "02", "02A")]

    generate_mock = MagicMock(return_value=SimpleNamespace(text="Live Gemini briefing message."))
    client_mock = MagicMock()
    client_mock.models.generate_content = generate_mock

    monkeypatch.setattr(gemini_client, "genai", SimpleNamespace(Client=lambda **k: client_mock))
    monkeypatch.setattr(gemini_client, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="mock-key",
        gemini_model="mock-model",
    ))

    res1 = _llm_briefing(items)
    assert res1 == "Live Gemini briefing message."
    assert generate_mock.call_count == 1

    # Second call for same items should hit cache
    res2 = _llm_briefing(items)
    assert res2 == "Live Gemini briefing message."
    assert generate_mock.call_count == 1


def test_llm_briefing_retries_on_transient_error(monkeypatch):
    gemini_client._CACHE.clear()
    items = [_make_anomaly("retry1", "03", "03A")]

    calls = {"count": 0}

    def flaky_generate(**kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            err = errors.APIError("Service Unavailable", None)
            err.code = 503
            raise err
        return SimpleNamespace(text="Recovered from 503.")

    client_mock = MagicMock()
    client_mock.models.generate_content = flaky_generate

    monkeypatch.setattr(gemini_client, "genai", SimpleNamespace(Client=lambda **k: client_mock))
    monkeypatch.setattr(gemini_client, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="mock-key",
        gemini_model="mock-model",
    ))
    monkeypatch.setattr(gemini_client, "time", SimpleNamespace(time=gemini_client.time.time, sleep=lambda s: None))

    res = _llm_briefing(items)
    assert res == "Recovered from 503."
    assert calls["count"] == 2


def test_verify_gemini_connection_unconfigured(monkeypatch):
    monkeypatch.setattr(gemini_client, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="",
        gemini_model="gemini-3.8-flash",
    ))
    res = verify_gemini_connection()
    assert res["status"] == "skipped"


def test_verify_gemini_connection_success(monkeypatch):
    client_mock = MagicMock()
    client_mock.models.generate_content = MagicMock(return_value=SimpleNamespace(text="Hello from Gemini!"))

    monkeypatch.setattr(gemini_client, "genai", SimpleNamespace(Client=lambda **k: client_mock))
    monkeypatch.setattr(gemini_client, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="valid-key",
        gemini_model="gemini-3.8-flash",
    ))

    res = verify_gemini_connection()
    assert res["status"] == "ok"
    assert res["model"] == "gemini-3.8-flash"
    assert res["response"] == "Hello from Gemini!"


def test_verify_endpoint(client, monkeypatch):
    monkeypatch.setattr(gemini_client, "verify_gemini_connection", lambda: {
        "status": "ok",
        "model": "gemini-3.8-flash",
        "response": "Hello!",
    })
    r = client.get("/api/v1/agent/verify")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["model"] == "gemini-3.8-flash"
