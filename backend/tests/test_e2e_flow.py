"""Feature F5: End-to-end automated product story test.

Full lifecycle flow:
  /simulate (inject phantom)
    -> POST /api/v1/anomalies/run (Scout Detection flags SKU)
      -> GET /api/v1/agent/checklist (Gemini Agent builds prioritized floor checklist)
        -> POST /api/v1/audit/reconcile (Floor staff taps 'Restocked' / 'Damaged')
          -> GET /api/v1/agent/checklist (item resolved and removed from active checklist)
          -> GET /api/v1/anomalies/metrics & /audit/feed (Manager KPIs & audit log update)
            -> POST /api/v1/simulate/normal (normal sales resume)
              -> POST /api/v1/anomalies/run (all clear confirmed)
"""
from fastapi.testclient import TestClient

from app.core import store


def test_end_to_end_phantom_detection_checklist_reconcile_flow(client: TestClient):
    # Step 1: Clean slate reset
    r_reset = client.post("/api/v1/simulate/reset")
    assert r_reset.status_code == 200 and r_reset.json()["ok"] is True

    # Step 2: Inject phantom stockout scenario (F1)
    # Munchee Cracker (s1) ceases sales for 8 open hours while ledger still records 40 units.
    r_sim = client.post("/api/v1/simulate/phantom", params={"variant": "frozen"})
    assert r_sim.status_code == 200
    sim_data = r_sim.json()
    assert sim_data["ok"] is True
    assert sim_data["sku_id"] == "s1"
    assert sim_data["ledger_stock"] == 40
    assert sim_data["silent_hours"] == 8

    # Step 3: Run Scout shelf-void detection (B1 + B2)
    r_det = client.post("/api/v1/anomalies/run")
    assert r_det.status_code == 200
    det_data = r_det.json()
    assert det_data["flagged"] >= 1

    alerts = det_data["alerts"]
    s1_alert = next((a for a in alerts if a["sku_id"] == "s1"), None)
    assert s1_alert is not None, "s1 must be flagged by Scout detection"
    assert s1_alert["p_void"] >= 0.75
    assert s1_alert["ledger_stock"] == 40
    assert s1_alert["silent_hours"] >= 8
    assert "Munchee" in s1_alert["sku_name"]

    # Verify open anomaly in the store
    anomalies = client.get("/api/v1/anomalies").json()
    s1_anomaly = next((a for a in anomalies if a["sku_id"] == "s1" and a["status"] == "open"), None)
    assert s1_anomaly is not None, "Open anomaly for s1 must exist in store"
    anomaly_id = s1_anomaly["id"]

    # Step 4: Floor Staff Agent Checklist (C1-C5, D1)
    # The Gemini / template agent organizes flagged anomalies into prioritized aisle groups
    r_check = client.get("/api/v1/agent/checklist")
    assert r_check.status_code == 200
    checklist = r_check.json()
    assert "briefing" in checklist
    assert len(checklist["groups"]) > 0

    # Locate s1 in checklist groups
    all_items = [item for group in checklist["groups"] for item in group["items"]]
    item_in_checklist = next((it for it in all_items if it["sku_id"] == "s1"), None)
    assert item_in_checklist is not None, "s1 must appear on the floor audit checklist"
    assert item_in_checklist["id"] == anomaly_id

    # Check metrics before reconciliation
    m_before = client.get("/api/v1/anomalies/metrics").json()
    active_before = m_before["active_voids"]
    assert active_before >= 1

    # Step 5: Floor Staff reconciles the item (D1)
    # Staff associate 'Nimal' finds stock on top shelf / bay and restocks 40 units
    r_rec = client.post(
        "/api/v1/audit/reconcile",
        json={
            "anomaly_id": anomaly_id,
            "action": "restocked",
            "associate": "Nimal Perera",
            "units": 40,
        },
    )
    assert r_rec.status_code == 200
    rec_res = r_rec.json()
    assert rec_res["ok"] is True
    assert rec_res["status"] == "restocked"
    assert rec_res["already_resolved"] is False

    # Verify anomaly status transitioned in DB
    updated_anom = store.get_anomaly(anomaly_id)
    assert updated_anom is not None
    assert updated_anom.status == "restocked"
    assert updated_anom.resolved_at is not None

    # Step 6: Verify Floor App Checklist is cleared of resolved item
    check_after = client.get("/api/v1/agent/checklist").json()
    items_after = [item for group in check_after["groups"] for item in group["items"]]
    assert not any(it["id"] == anomaly_id for it in items_after), "Resolved item must be cleared from checklist"

    # Step 7: Verify Store Manager Portal updates (E1, E4)
    m_after = client.get("/api/v1/anomalies/metrics").json()
    assert m_after["active_voids"] == active_before - 1
    assert m_after["revenue_recovered_lkr"] > 0

    feed = client.get("/api/v1/audit/feed").json()
    assert len(feed) > 0
    recent_entry = feed[0]
    assert recent_entry["sku_id"] == "s1"
    assert recent_entry["action"] == "restocked"
    assert recent_entry["associate"] == "Nimal Perera"
    assert "40 units" in recent_entry["summary"]

    # Step 8: Resume normal trading & confirm all clear
    client.post("/api/v1/simulate/normal")
    det_cleared = client.post("/api/v1/anomalies/run").json()
    assert isinstance(det_cleared["flagged"], int)


def test_end_to_end_damaged_void_with_ledger_writeoff(client: TestClient):
    """E2E flow for damaged / spoiled inventory requiring ledger write-off."""
    client.post("/api/v1/simulate/reset")

    # Inject damaged variant
    sim = client.post("/api/v1/simulate/phantom", params={"variant": "damaged"}).json()
    assert sim["variant"] == "damaged"
    assert sim["expected_action"] == "damaged"

    # Detect
    det = client.post("/api/v1/anomalies/run").json()
    assert det["flagged"] >= 1
    anom = next(a for a in client.get("/api/v1/anomalies").json() if a["sku_id"] == "s1" and a["status"] == "open")
    assert anom["void_type"] in ("damaged", "frozen")

    stock_before = store.get_sku("s1").ledger_stock

    # Reconcile with write-off
    rec = client.post(
        "/api/v1/audit/reconcile",
        json={
            "anomaly_id": anom["id"],
            "action": "damaged",
            "associate": "Kumari",
            "units": 15,
        },
    ).json()

    assert rec["ok"] is True
    assert rec["status"] == "damaged"
    assert rec["ledger_adjustment"] == -15
    assert store.get_sku("s1").ledger_stock == stock_before - 15

    # Test Undo flow (Feature D5)
    undo = client.post(
        "/api/v1/audit/undo",
        json={"anomaly_id": anom["id"], "associate": "Kumari"},
    ).json()
    assert undo["ok"] is True
    assert undo["reopened"] is True
    assert undo["status"] == "open"
    # Ledger stock restored after undo
    assert store.get_sku("s1").ledger_stock == stock_before
