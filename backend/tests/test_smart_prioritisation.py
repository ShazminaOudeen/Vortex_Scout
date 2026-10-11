"""Tests for Smart Prioritisation & Walk Path Ordering (Feature C2)."""
from datetime import datetime, timezone
import pytest

from app.agent.gemini_client import (
    _aisle_sort_key,
    _bay_sort_key,
    _group,
    _item_walk_key,
    _template_briefing,
    build_checklist,
    prioritize_anomalies,
)
from app.core import store
from app.models.anomaly import Anomaly


def _anomaly(
    id_: str,
    sku_name: str,
    aisle: str,
    bay: str,
    revenue_at_risk: float,
    p_void: float = 0.85,
    unit_price: float = 100.0,
) -> Anomaly:
    return Anomaly(
        id=id_,
        sku_id=f"SKU-{id_}",
        sku_name=sku_name,
        aisle=aisle,
        bay=bay,
        category="Groceries",
        p_void=p_void,
        ledger_stock=10,
        hours_since_last_sale=5.0,
        unit_price=unit_price,
        revenue_at_risk=revenue_at_risk,
        priority_score=round(revenue_at_risk * p_void, 2),
        detected_at=datetime.now(timezone.utc),
    )


def test_prioritize_anomalies_ranks_by_revenue_at_risk():
    """Higher revenue at risk ranks higher than lower revenue even with lower p_void."""
    a1 = _anomaly("1", "Low Rev High Prob", "02", "02A", revenue_at_risk=250.0, p_void=0.95)
    a2 = _anomaly("2", "High Rev Lower Prob", "05", "05A", revenue_at_risk=5000.0, p_void=0.75)
    a3 = _anomaly("3", "Mid Rev", "01", "01A", revenue_at_risk=1200.0, p_void=0.80)

    ranked = prioritize_anomalies([a1, a2, a3])
    assert [a.id for a in ranked] == ["2", "3", "1"]


def test_prioritize_anomalies_tie_breakers():
    """Ties on revenue at risk break by p_void, then physical location."""
    a1 = _anomaly("1", "Same Rev Lower Prob", "02", "02A", revenue_at_risk=1000.0, p_void=0.80)
    a2 = _anomaly("2", "Same Rev Higher Prob", "04", "04A", revenue_at_risk=1000.0, p_void=0.90)
    a3 = _anomaly("3", "Same Rev Same Prob Bay B", "02", "02B", revenue_at_risk=500.0, p_void=0.85)
    a4 = _anomaly("4", "Same Rev Same Prob Bay A", "02", "02A", revenue_at_risk=500.0, p_void=0.85)

    ranked = prioritize_anomalies([a1, a2, a3, a4])
    assert ranked[0].id == "2"  # higher p_void (0.90 vs 0.80)
    assert ranked[1].id == "1"
    assert ranked[2].id == "4"  # bay 02A before 02B
    assert ranked[3].id == "3"


def test_aisle_and_bay_sorting_walk_path():
    """Aisles and bays sort naturally according to physical walk sequence."""
    assert _aisle_sort_key("2") < _aisle_sort_key("10")
    assert _aisle_sort_key("02") < _aisle_sort_key("11")
    assert _bay_sort_key("01A") < _bay_sort_key("01B")
    assert _bay_sort_key("01B") < _bay_sort_key("02A")
    assert _bay_sort_key("10A") > _bay_sort_key("02A")

    items = [
        _anomaly("1", "Item Bay 02B", "02", "02B", revenue_at_risk=100.0),
        _anomaly("2", "Item Bay 02A", "02", "02A", revenue_at_risk=100.0),
        _anomaly("3", "Item Aisle 01", "01", "01A", revenue_at_risk=200.0),
        _anomaly("4", "Item Aisle 10", "10", "10A", revenue_at_risk=50.0),
    ]
    groups = _group(items)
    assert [g.aisle for g in groups] == ["01", "02", "10"]
    # Within aisle 02, bay 02A comes before 02B
    assert [i.id for i in groups[1].items] == ["2", "1"]


def test_build_checklist_calculates_total_revenue_at_risk():
    """Checklist computes total revenue at risk and formats briefing recommendation."""
    items = [
        _anomaly("1", "Munchee Biscuits", "02", "02A", revenue_at_risk=4500.0),
        _anomaly("2", "Anchor Milk", "04", "04B", revenue_at_risk=8000.0),
    ]
    cl = build_checklist(items)
    assert cl.total_revenue_at_risk == 12500.0
    assert "LKR 12,500 at risk" in cl.briefing
    assert "Start in Aisle 04 (Anchor Milk)" in cl.briefing


def test_detection_run_annotates_revenue_at_risk_and_priority_score(client):
    """Detection run populates unit_price, revenue_at_risk, and priority_score on alerts and anomalies."""
    client.post("/api/v1/simulate/phantom")
    r = client.post("/api/v1/anomalies/run").json()
    assert r["flagged"] >= 1
    alert = next(a for a in r["alerts"] if a["sku_id"] == "s1")
    assert "revenue_at_risk" in alert
    assert "priority_score" in alert
    assert alert["revenue_at_risk"] > 0
    assert alert["priority_score"] > 0

    # Stored anomaly also retains revenue_at_risk and priority_score
    anomalies = client.get("/api/v1/anomalies").json()
    s1_anom = next(a for a in anomalies if a["sku_id"] == "s1" and a["status"] == "open")
    assert s1_anom["revenue_at_risk"] == alert["revenue_at_risk"]
    assert s1_anom["priority_score"] == alert["priority_score"]


def test_agent_checklist_api_includes_revenue_and_prioritisation(client):
    """GET /api/v1/agent/checklist returns total_revenue_at_risk and aisle groupings."""
    client.post("/api/v1/simulate/phantom")
    client.post("/api/v1/anomalies/run")
    resp = client.get("/api/v1/agent/checklist")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_revenue_at_risk" in data
    assert data["total_revenue_at_risk"] > 0
    assert len(data["groups"]) >= 1
    first_item = data["groups"][0]["items"][0]
    assert "revenue_at_risk" in first_item
    assert "priority_score" in first_item
