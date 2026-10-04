import pandas as pd

from app.core import store
from app.ml.feature_pipeline import get_velocity, hours_since_last_sale


def sim(client, name, **params):
    return client.post(f"/api/v1/simulate/{name}", params=params)


def test_phantom_on_an_empty_store_builds_history_and_freezes_the_munchee_sku(client):
    r = sim(client, "phantom")
    body = r.json()
    assert r.status_code == 200 and body["scenario"] == "phantom"
    assert (body["sku_id"], body["ledger_stock"], body["silent_hours"]) == ("s1", 40, 8)
    assert body["ingested"] > 5000 and body["rejected"] == 0
    assert store.get_sku("s1").ledger_stock == 40

    v = get_velocity()
    s1 = v[v.sku_id == "s1"].sort_values("hour")
    assert (s1.units.tail(8) == 0).all()                       # 0 sales for 8 trading hours
    assert s1.units.iloc[:-8].sum() > 100                      # after a normal week
    assert v[v.sku_id == "s2"].units.tail(8).sum() > 0         # the rest of the store is fine
    assert hours_since_last_sale().set_index("sku_id").loc["s1", "hours_since_last_sale"] >= 8


def test_phantom_appends_to_existing_history_instead_of_double_counting(client):
    sim(client, "normal")                                      # history exists now
    latest = store.latest_velocity_hour()
    before = get_velocity()
    assert sim(client, "phantom").json()["window_start"] > latest.isoformat()
    after = get_velocity()
    overlap = after[after.hour <= before.hour.max()].set_index(["sku_id", "hour"]).units
    assert overlap.equals(before.set_index(["sku_id", "hour"]).units)  # old hours untouched
    assert store.latest_velocity_hour() > latest
    s1 = after[after.sku_id == "s1"].sort_values("hour")
    assert (s1.units.tail(8) == 0).all()


def test_normal_pushes_peak_traffic_for_every_sku_and_advances_the_data_clock(client):
    sim(client, "normal")
    latest = store.latest_velocity_hour()
    r = sim(client, "normal").json()
    assert r["hours"] == 3 and r["ingested"] > 300
    assert store.latest_velocity_hour() > latest
    v = get_velocity(since=pd.Timestamp(r["window_start"]).to_pydatetime())
    assert v.groupby("hour").units.sum().min() > 100           # busy in every hour of the window
    assert v[v.sku_id == "s1"].units.sum() > 0


def test_phantom_variants(client):
    assert sim(client, "phantom", variant="damaged").json()["expected_action"] == "damaged"
    assert sim(client, "reset").json()["ok"] is True
    body = sim(client, "phantom", variant="backroom_stuck").json()
    assert body["variant"] == "backroom_stuck"
    s1 = get_velocity(sku_id="s1")
    assert (s1.units.tail(4) == 0).all()                       # taper is done after 3 hours


def test_unknown_variant_or_scenario_is_422(client):
    assert sim(client, "phantom", variant="stolen").status_code == 422
    assert sim(client, "explode").status_code == 422


def test_reset_clears_data_and_restores_ledger_and_demo_anomalies(client):
    sim(client, "phantom")
    a = next(a for a in client.get("/api/v1/anomalies").json() if a["sku_id"] == "s2")
    client.post("/api/v1/audit/reconcile", json={"anomaly_id": a["id"], "action": "damaged", "units": 10})
    assert store.latest_velocity_hour() is not None and store.list_audit() and store.get_sku("s2").ledger_stock == 22

    assert sim(client, "reset").json() == {"ok": True, "scenario": "reset"}
    assert store.latest_velocity_hour() is None and store.list_hourly_velocity() == []
    assert store.list_audit() == []
    assert store.get_sku("s1").ledger_stock == 70 and store.get_sku("s2").ledger_stock == 32
    anomalies = client.get("/api/v1/anomalies").json()
    assert sorted(x["sku_id"] for x in anomalies) == ["s1", "s2", "s3"]
    assert all(x["status"] == "open" for x in anomalies)
