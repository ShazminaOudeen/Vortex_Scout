"""Tests for 'Why was this flagged?' plain-English explanations (Feature C3)."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest

from app.agent import explainer
from app.agent.explainer import (
    explain_anomaly,
    explain_anomaly_details,
    format_hours_str,
    format_rate_str,
    llm_explanation,
    template_explanation,
)
from app.core import store
from app.models.anomaly import Anomaly


def test_format_helpers():
    assert format_rate_str(4.0) == "4/hr"
    assert format_rate_str(3.5) == "3.5/hr"
    assert format_hours_str(1.0) == "1 hour"
    assert format_hours_str(9.2) == "9 hours"


def test_template_explanation_frozen():
    """Default shelf void explains sales rate, silent hours, and ledger count."""
    msg = template_explanation(
        sku_name="Munchee Super Cream Cracker",
        rate=4.0,
        hours=9.0,
        ledger=32,
        void_type="frozen",
    )
    assert msg == "Usually sells 4/hr at this time, none in 9 hours, ledger says 32."


def test_template_explanation_damaged():
    """Damaged void highlights breakage/perishable category risk."""
    msg = template_explanation(
        sku_name="Anchor Fresh Milk",
        rate=2.5,
        hours=5.0,
        ledger=18,
        void_type="damaged",
        category="Chilled Dairy",
    )
    assert "high damage/breakage risk in Chilled Dairy" in msg
    assert "Usually sells 2.5/hr" in msg


def test_template_explanation_backroom_stuck():
    """Backroom stuck void mentions tapering and unreplenished stock."""
    msg = template_explanation(
        sku_name="Maliban Gold Marie",
        rate=3.0,
        hours=8.0,
        ledger=45,
        void_type="backroom_stuck",
    )
    assert "Sales tapered to zero" in msg
    assert "suspected backroom stock not replenished to shelf" in msg


def test_llm_explanation_generates_and_caches(monkeypatch):
    """LLM explanation calls Gemini with system instruction and caches the result."""
    explainer._EXPLAIN_CACHE.clear()

    generate_mock = MagicMock(return_value=SimpleNamespace(text="Sells 4/hr normally, silent for 9 hours with 32 on ledger."))
    client_mock = MagicMock()
    client_mock.models.generate_content = generate_mock

    monkeypatch.setattr(explainer, "genai", SimpleNamespace(Client=lambda **k: client_mock))
    monkeypatch.setattr(explainer, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="mock-key",
        gemini_model="gemini-3.8-flash",
    ))

    res1 = llm_explanation("Product A", 4.0, 9.0, 32, "frozen")
    assert res1 == "Sells 4/hr normally, silent for 9 hours with 32 on ledger."
    assert generate_mock.call_count == 1

    # Second call should hit cache
    res2 = llm_explanation("Product A", 4.0, 9.0, 32, "frozen")
    assert res2 == res1
    assert generate_mock.call_count == 1


def test_llm_explanation_falls_back_to_template_on_error(monkeypatch):
    """Network or API error gracefully falls back to template explanation."""
    monkeypatch.setattr(explainer, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="mock-key",
        gemini_model="gemini-3.8-flash",
    ))

    def fail_client(**kwargs):
        raise RuntimeError("API timeout")

    monkeypatch.setattr(explainer, "genai", SimpleNamespace(Client=fail_client))

    res = explain_anomaly("Product B", 2.0, 6.0, 20, "frozen", use_llm=True)
    assert "Usually sells 2/hr at this time, none in 6 hours, ledger says 20." in res


def test_detection_run_populates_why_flagged_on_alerts(client):
    """POST /anomalies/run outputs why_flagged on all alerts and stored anomalies."""
    client.post("/api/v1/simulate/phantom")
    r = client.post("/api/v1/anomalies/run").json()
    assert r["flagged"] >= 1
    s1 = next(a for a in r["alerts"] if a["sku_id"] == "s1")
    assert "why_flagged" in s1 and len(s1["why_flagged"]) > 10
    assert "none in" in s1["why_flagged"] or "Sales tapered" in s1["why_flagged"]

    anomalies = client.get("/api/v1/anomalies").json()
    open_a = [a for a in anomalies if a["status"] == "open"]
    for a in open_a:
        assert a.get("why_flagged")
        assert len(a["why_flagged"]) > 0


def test_explain_endpoint(client):
    """GET /anomalies/{id}/explain returns explanation and factors."""
    client.post("/api/v1/simulate/phantom")
    client.post("/api/v1/anomalies/run")
    anomalies = client.get("/api/v1/anomalies").json()
    aid = anomalies[0]["id"]

    resp = client.get(f"/api/v1/anomalies/{aid}/explain?use_gemini=false")
    assert resp.status_code == 200
    data = resp.json()
    assert data["anomaly_id"] == aid
    assert data["why_flagged"]
    assert "factors" in data
    assert data["factors"]["hours_since_last_sale"] > 0
    assert data["factors"]["ledger_stock"] >= 0


def test_explain_endpoint_404_on_unknown(client):
    resp = client.get("/api/v1/anomalies/non-existent-id/explain")
    assert resp.status_code == 404


def test_checklist_items_contain_why_flagged(client):
    """GET /agent/checklist items include why_flagged string for display on mobile floor cards."""
    client.post("/api/v1/simulate/phantom")
    client.post("/api/v1/anomalies/run")
    resp = client.get("/api/v1/agent/checklist")
    assert resp.status_code == 200
    checklist = resp.json()
    assert len(checklist["groups"]) > 0
    for g in checklist["groups"]:
        for it in g["items"]:
            assert "why_flagged" in it and len(it["why_flagged"]) > 0
