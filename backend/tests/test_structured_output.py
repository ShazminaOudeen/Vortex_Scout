"""Tests for Gemini Structured JSON Output (Feature C4)."""
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest

from app.agent import gemini_client
from app.agent.gemini_client import (
    _compute_priority_level,
    _llm_structured_plan,
    _template_plan,
    build_checklist,
    generate_agent_plan,
)
from app.models.anomaly import Anomaly, ChecklistAgentPlan, ItemStructuredAdvice


def _make_item(id_: str, sku_id: str, rev: float, p_void: float = 0.85, action: str = "restocked") -> Anomaly:
    return Anomaly(
        id=id_,
        sku_id=sku_id,
        sku_name=f"Product {id_}",
        aisle="03",
        bay="03A",
        category="Groceries",
        ledger_stock=24,
        hours_since_last_sale=6.0,
        p_void=p_void,
        unit_price=100.0,
        revenue_at_risk=rev,
        priority_score=round(rev * p_void, 2),
        suggested_action=action,
        detected_at=datetime.now(timezone.utc),
    )


def test_compute_priority_level():
    crit = _make_item("1", "s1", rev=6000.0, p_void=0.90)
    assert _compute_priority_level(crit) == "critical"

    high = _make_item("2", "s2", rev=1800.0, p_void=0.70)
    assert _compute_priority_level(high) == "high"

    med = _make_item("3", "s3", rev=600.0, p_void=0.76)
    assert _compute_priority_level(med) == "medium"

    low = _make_item("4", "s4", rev=200.0, p_void=0.60)
    assert _compute_priority_level(low) == "low"


def test_template_plan_generation():
    items = [
        _make_item("1", "s1", rev=4000.0, p_void=0.88),
        _make_item("2", "s2", rev=1200.0, p_void=0.82),
    ]
    plan = _template_plan(items)
    assert isinstance(plan, ChecklistAgentPlan)
    assert "detected in aisle 03" in plan.briefing
    assert "LKR 5,200 at risk" in plan.briefing
    assert plan.start_aisle == "03"
    assert len(plan.items) == 2
    assert plan.items[0].sku_id == "s1"
    assert plan.items[0].priority in ("critical", "high", "medium", "low")
    assert plan.items[0].suggested_action == "restocked"


def test_template_plan_empty():
    plan = _template_plan([])
    assert isinstance(plan, ChecklistAgentPlan)
    assert plan.items == []
    assert "No likely shelf voids" in plan.briefing


def test_llm_structured_plan_parses_typed_schema(monkeypatch):
    gemini_client._PLAN_CACHE.clear()
    items = [_make_item("c4_1", "s1", rev=3000.0)]

    mock_plan_dict = {
        "briefing": "High priority void in Aisle 03 for Product c4_1 (~LKR 3,000 at risk).",
        "start_aisle": "03",
        "items": [
            {
                "sku_id": "s1",
                "priority": "critical",
                "reason": "Sales stopped 6h ago despite 24 units in ledger.",
                "suggested_action": "restocked",
            }
        ],
    }

    generate_mock = MagicMock(return_value=SimpleNamespace(text=json.dumps(mock_plan_dict)))
    client_mock = MagicMock()
    client_mock.models.generate_content = generate_mock

    monkeypatch.setattr(gemini_client, "genai", SimpleNamespace(Client=lambda **k: client_mock))
    monkeypatch.setattr(gemini_client, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="mock-key",
        gemini_model="gemini-3.8-flash",
    ))

    plan = _llm_structured_plan(items)
    assert isinstance(plan, ChecklistAgentPlan)
    assert plan.briefing == mock_plan_dict["briefing"]
    assert plan.start_aisle == "03"
    assert len(plan.items) == 1
    assert plan.items[0].priority == "critical"
    assert plan.items[0].suggested_action == "restocked"
    assert generate_mock.call_count == 1

    # Call again with same items -> should hit cache
    cached_plan = _llm_structured_plan(items)
    assert cached_plan.briefing == mock_plan_dict["briefing"]
    assert generate_mock.call_count == 1


def test_llm_structured_plan_falls_back_on_error(monkeypatch):
    items = [_make_item("err1", "s1", rev=2500.0)]
    monkeypatch.setattr(gemini_client, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="mock-key",
        gemini_model="gemini-3.8-flash",
    ))

    def fail_llm(**kwargs):
        raise RuntimeError("LLM schema failure")

    monkeypatch.setattr(gemini_client, "genai", SimpleNamespace(Client=fail_llm))

    plan = generate_agent_plan(items, use_llm=True)
    assert isinstance(plan, ChecklistAgentPlan)
    assert "detected in aisle 03" in plan.briefing
    assert len(plan.items) == 1


def test_build_checklist_attaches_structured_plan(monkeypatch):
    items = [_make_item("b1", "s1", rev=5000.0)]
    monkeypatch.setattr(gemini_client, "get_settings", lambda: SimpleNamespace(
        gemini_api_key="",
        gemini_model="gemini-3.8-flash",
    ))

    cl = build_checklist(items)
    assert cl.plan is not None
    assert isinstance(cl.plan, ChecklistAgentPlan)
    assert len(cl.groups) == 1
    item = cl.groups[0].items[0]
    assert item.priority_level == "critical"


def test_agent_plan_endpoint(client):
    """GET /api/v1/agent/plan returns typed structured plan JSON."""
    client.post("/api/v1/simulate/phantom")
    client.post("/api/v1/anomalies/run")

    resp = client.get("/api/v1/agent/plan?use_gemini=false")
    assert resp.status_code == 200
    data = resp.json()
    assert "briefing" in data
    assert "start_aisle" in data
    assert "items" in data
    assert len(data["items"]) >= 1
    assert "priority" in data["items"][0]
    assert "suggested_action" in data["items"][0]


def test_checklist_endpoint_includes_plan(client):
    """GET /api/v1/agent/checklist includes plan."""
    client.post("/api/v1/simulate/phantom")
    client.post("/api/v1/anomalies/run")

    resp = client.get("/api/v1/agent/checklist")
    assert resp.status_code == 200
    data = resp.json()
    assert "plan" in data
    assert data["plan"] is not None
    assert "items" in data["plan"]
