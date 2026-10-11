"""Tests for Manager Portal (Module 5): Features E1 to E6.

Runs against both in-memory and fake Supabase backends via the parameterized `client` fixture.
"""
from datetime import datetime

import pytest

from app.core import store
from app.generator.generate_mock_pos import generate
from app.services.ingest import ingest


def test_real_kpis_computation(client):
    """Feature E1: Real KPIs computed from store state."""
    # Initially demo store has 3 demo anomalies and 200 SKUs
    anomalies = client.get("/api/v1/anomalies").json()
    assert len(anomalies) == 3
    s1_anom = next(a for a in anomalies if a["sku_id"] == "s1")

    res = client.get("/api/v1/anomalies/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["active_voids"] == 3
    assert data["audit_completion_rate"] == 0.0
    assert data["revenue_recovered_lkr"] == 0.0
    # 3 active SKUs out of 200 SKUs = 0.015 (1.5%)
    assert data["iri_rate"] == pytest.approx(3 / 200, rel=1e-2)
    assert len(data["category_breakdown"]) > 0
    total_share = sum(c["share"] for c in data["category_breakdown"])
    assert total_share == pytest.approx(100.0, abs=1.0)

    # Now reconcile one anomaly as restocked with 20 units
    reconcile_res = client.post(
        "/api/v1/audit/reconcile",
        json={"anomaly_id": s1_anom["id"], "action": "restocked", "associate": "Nimal", "units": 20},
    )
    assert reconcile_res.status_code == 200

    # Re-fetch metrics: active_voids should decrease to 2, completion rate should be 1/3 ~ 33.3%
    metrics_res = client.get("/api/v1/anomalies/metrics")
    assert metrics_res.status_code == 200
    updated = metrics_res.json()
    assert updated["active_voids"] == 2
    assert updated["audit_completion_rate"] == pytest.approx(1 / 3, rel=1e-2)
    # Revenue recovered should be 20 * unit_price of s1
    sku_s1 = store.get_sku("s1")
    assert sku_s1 is not None
    expected_revenue = 20 * sku_s1.unit_price
    assert updated["revenue_recovered_lkr"] == pytest.approx(expected_revenue, rel=1e-2)


def test_velocity_endpoints(client):
    """Feature E2: Expected vs actual velocity for anomalies and SKUs."""
    anomalies = client.get("/api/v1/anomalies").json()
    s1_anom = next(a for a in anomalies if a["sku_id"] == "s1")

    # When no POS transactions are loaded, endpoints return has_data=False and empty points
    res_anom = client.get(f"/api/v1/anomalies/{s1_anom['id']}/velocity")
    assert res_anom.status_code == 200
    v_data = res_anom.json()
    assert v_data["sku_id"] == "s1"
    assert v_data["has_data"] is False
    assert v_data["points"] == []


    # Check 404 for non-existent anomaly
    assert client.get("/api/v1/anomalies/non_existent/velocity").status_code == 404

    # SKU velocity
    res_sku = client.get("/api/v1/skus/s1/velocity")
    assert res_sku.status_code == 200
    assert res_sku.json()["sku_id"] == "s1"
    assert client.get("/api/v1/skus/unknown_sku/velocity").status_code == 404

    # Now load mock transactions to test velocity curve computation
    df = generate(days=2, phantom_sku="s1", phantom_hours=8, end=datetime(2026, 10, 3, 22, 0))
    ingest_res = ingest(df.to_dict("records"))
    assert ingest_res.rejected == 0

    # Verify velocity response contains real curve points
    res_loaded = client.get("/api/v1/skus/s1/velocity")
    assert res_loaded.status_code == 200
    loaded_data = res_loaded.json()
    assert loaded_data["has_data"] is True
    points = loaded_data["points"]
    assert len(points) > 0
    # Verify shape of points: hour, expected, actual
    for pt in points:
        assert "hour" in pt
        assert "expected" in pt
        assert "actual" in pt
        assert pt["expected"] >= 0
        assert pt["actual"] >= 0

    # For phantom SKU s1, trailing hours should show actual == 0 while expected > 0
    silent_tail = points[-8:]
    assert all(pt["actual"] == 0 for pt in silent_tail)
    assert any(pt["expected"] > 0 for pt in silent_tail)


def test_recent_reconciliations_feed(client):
    """Feature E4: Recent reconciliations feed with human-readable descriptions."""
    # Initially feed is empty
    init_feed = client.get("/api/v1/audit/feed").json()
    assert init_feed == []

    anomalies = client.get("/api/v1/anomalies").json()
    s1_anom = next(a for a in anomalies if a["sku_id"] == "s1")

    # Log restock action
    client.post(
        "/api/v1/audit/reconcile",
        json={"anomaly_id": s1_anom["id"], "action": "restocked", "associate": "Nimal", "units": 24},
    )

    feed = client.get("/api/v1/audit/feed").json()
    assert len(feed) == 1
    item = feed[0]
    assert item["anomaly_id"] == s1_anom["id"]
    assert item["sku_id"] == "s1"
    assert item["action"] == "restocked"
    assert item["associate"] == "Nimal"
    assert item["units"] == 24
    assert "Munchee" in item["summary"]
    assert "24 units" in item["summary"]
    assert "Nimal" in item["summary"]


def test_full_sku_inventory_explorer(client):
    """Feature E5: Full 200-SKU catalog listing with risk indicators."""
    res = client.get("/api/v1/skus")
    assert res.status_code == 200
    skus = res.json()
    assert len(skus) == 200

    # Check that each SKU has the required contract fields
    s1 = next(s for s in skus if s["id"] == "s1")
    assert s1["has_open_anomaly"] is True
    assert s1["anomaly_status"] == "open"
    assert s1["p_void"] >= 0.75
    assert s1["risk_level"] == "critical"

    # Non-anomalous SKU
    s10 = next(s for s in skus if s["id"] == "s10")
    assert s10["has_open_anomaly"] is False
    assert s10["risk_level"] == "normal"


def test_sku_detail_endpoint(client):
    """Feature E6: Detailed product drill-down."""
    # Check 404
    assert client.get("/api/v1/skus/unknown_sku_999").status_code == 404

    anomalies = client.get("/api/v1/anomalies").json()
    s1_anom = next(a for a in anomalies if a["sku_id"] == "s1")

    # Check s1
    res = client.get("/api/v1/skus/s1")
    assert res.status_code == 200
    detail = res.json()
    assert detail["sku"]["id"] == "s1"
    assert detail["sku"]["name"] == "Munchee Super Cream Cracker 490g"
    assert detail["open_anomaly"] is not None
    assert detail["open_anomaly"]["id"] == s1_anom["id"]
    assert isinstance(detail["audit_history"], list)

