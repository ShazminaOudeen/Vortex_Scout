"""B1 + B2: baseline shelf-void detector and the POST /anomalies/run endpoint."""
from datetime import datetime

import pandas as pd
import pytest

from app.core import store
from app.generator.catalog import load_catalog
from app.generator.generate_mock_pos import generate
from app.ml.baseline import MIN_SILENT_HOURS, OUTPUT_COLUMNS, score_voids
from app.ml.feature_pipeline import add_time_features, get_velocity
from app.services.ingest import ingest

END = datetime(2026, 10, 3, 22, 0)  # a Saturday; last open hour is 21:00
THRESHOLD = 0.75


def sim(client, name, **params):
    return client.post(f"/api/v1/simulate/{name}", params=params)


def run(client):
    r = client.post("/api/v1/anomalies/run")
    assert r.status_code == 200
    return r.json()


def open_skus(client):
    return sorted(a["sku_id"] for a in client.get("/api/v1/anomalies").json() if a["status"] == "open")


def silence(frame: pd.DataFrame, sku_id: str, hours: int) -> pd.DataFrame:
    """Copy of a dense velocity frame with the SKU's last `hours` open hours set to zero sales."""
    out = frame.copy()
    out.loc[out[out.sku_id == sku_id].sort_values("hour").tail(hours).index, "units"] = 0
    return out


@pytest.fixture
def week(backend):
    """A week of normal trading in the store, as the dense frame the detector reads."""
    ingest(generate(days=7, end=END, seed=3).to_dict("records"))
    return get_velocity()


# ---------------------------------------------------------------- the scorer (B1)
def test_empty_frame_scores_nothing(backend):
    out = score_voids(get_velocity())
    assert out.empty and list(out.columns) == OUTPUT_COLUMNS


def test_one_row_per_sku_with_the_documented_columns(week):
    out = score_voids(week)
    assert list(out.columns) == OUTPUT_COLUMNS
    assert len(out) == 200 and out.sku_id.is_unique
    assert out.p_void.between(0, 1).all()


def test_normal_trading_flags_nothing(week):
    assert (score_voids(week).p_void < THRESHOLD).all()


def test_a_fast_seller_that_goes_silent_is_flagged(week):
    out = score_voids(silence(week, "s1", 8)).set_index("sku_id")
    assert out.loc["s1", "silent_hours"] == 8
    assert out.loc["s1", "p_void"] >= THRESHOLD
    assert out.loc["s1", "expected_sales"] > 20            # we expected to see plenty of sales
    assert (out.drop(index="s1").p_void < THRESHOLD).all()  # and nothing else is flagged


def test_the_same_silence_on_a_slow_seller_is_not_flagged(week):
    slow = next(s["id"] for s in load_catalog() if s["base_rate"] < 0.15)
    out = score_voids(silence(week, slow, 14)).set_index("sku_id")  # a whole trading day of silence
    assert out.loc[slow, "p_void"] < THRESHOLD


def test_more_silence_means_more_suspicion(week):
    mid = next(s["id"] for s in load_catalog() if 0.4 <= s["base_rate"] <= 0.5)  # not fast enough to saturate
    rows = [score_voids(silence(week, mid, h)).set_index("sku_id").loc[mid] for h in (4, 6, 8)]
    pairs = sorted((int(r.silent_hours), r.p_void) for r in rows)  # the SKU may have been quiet a bit longer
    assert [p for _, p in pairs] == sorted(p for _, p in pairs)
    assert pairs[0][1] < pairs[-1][1]


def test_a_short_silence_is_never_flagged(week):
    out = score_voids(silence(week, "s1", MIN_SILENT_HOURS - 1)).set_index("sku_id")
    assert out.loc["s1", "p_void"] == 0.0


def test_a_sku_with_too_little_history_is_not_scored(backend):
    rows = pd.DataFrame({"sku_id": "new", "hour": pd.date_range("2026-10-03 08:00", periods=10, freq="h"),
                         "units": [3, 2, 4, 3, 2, 0, 0, 0, 0, 0]})
    out = score_voids(add_time_features(rows))
    assert out.loc[0, "p_void"] == 0.0


def test_a_sku_that_never_sold_is_not_flagged(week):
    w = week.copy()
    w.loc[w.sku_id == "s9", "units"] = 0
    out = score_voids(w).set_index("sku_id")
    assert out.loc["s9", "p_void"] == 0.0


# ---------------------------------------------------------------- the endpoint (B2)
def test_run_on_an_empty_store_changes_nothing(client):
    r = run(client)
    assert r["flagged"] == 0 and r["note"] and r["data_as_of"] is None
    assert open_skus(client) == ["s1", "s2", "s3"]  # the demo alerts are left alone


def test_phantom_then_run_flags_munchee_and_replaces_the_sample_alerts(client):
    sim(client, "phantom")
    r = run(client)
    assert r["flagged"] >= 1
    s1 = next(a for a in r["alerts"] if a["sku_id"] == "s1")
    assert s1["p_void"] >= THRESHOLD and s1["silent_hours"] == 8 and s1["ledger_stock"] == 40
    assert s1["sku_name"].startswith("Munchee") and s1["aisle"] == "03" and s1["bay"] == "3B"
    assert r["created"] + r["updated"] == r["flagged"]
    assert r["cleared"] >= 2                                    # Highland and Anchor were not real voids
    assert open_skus(client) == sorted(a["sku_id"] for a in r["alerts"])
    assert "s2" not in open_skus(client) and "s3" not in open_skus(client)


def test_the_floor_checklist_shows_the_detected_alert(client):
    sim(client, "phantom")
    run(client)
    groups = client.get("/api/v1/agent/checklist").json()["groups"]
    items = [i for g in groups for i in g["items"]]
    assert [i["sku_id"] for i in items] == ["s1"]
    assert items[0]["p_void"] >= THRESHOLD and items[0]["hours_since_last_sale"] >= 8


def test_running_twice_does_not_duplicate_or_churn_alerts(client):
    sim(client, "phantom")
    first = run(client)
    ids = {a["id"] for a in client.get("/api/v1/anomalies").json() if a["status"] == "open"}
    second = run(client)
    assert second["created"] == 0 and second["cleared"] == 0 and second["updated"] == first["flagged"]
    assert {a["id"] for a in client.get("/api/v1/anomalies").json() if a["status"] == "open"} == ids


@pytest.mark.parametrize("variant", ["frozen", "damaged", "backroom_stuck"])
def test_every_phantom_variant_is_caught(client, variant):
    sim(client, "phantom", variant=variant)
    assert "s1" in [a["sku_id"] for a in run(client)["alerts"]]


def test_a_sku_the_ledger_already_shows_as_empty_is_not_flagged(client):
    sim(client, "phantom")
    store.set_ledger_stock("s1", 0)
    r = run(client)
    assert "s1" not in [a["sku_id"] for a in r["alerts"]] and r["ledger_zero_skipped"] == 1
    assert "s1" not in open_skus(client)


def test_resolved_alerts_are_kept_and_sales_resuming_clears_the_flag(client):
    sim(client, "phantom")
    run(client)
    a = next(x for x in client.get("/api/v1/anomalies").json() if x["sku_id"] == "s1" and x["status"] == "open")
    assert client.post("/api/v1/audit/reconcile", json={"anomaly_id": a["id"], "action": "restocked"}).json()["ok"]

    sim(client, "normal")                                       # the shelf is refilled, sales resume
    r = run(client)
    assert "s1" not in [x["sku_id"] for x in r["alerts"]]
    assert open_skus(client) == []
    kept = next(x for x in client.get("/api/v1/anomalies").json() if x["id"] == a["id"])
    assert kept["status"] == "restocked"                        # history untouched
    assert len(store.list_audit()) == 1
