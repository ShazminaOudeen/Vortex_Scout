import time
from datetime import datetime

from app.core import store
from app.core.config import get_settings
from app.generator.generate_mock_pos import generate

ROW = {"timestamp": "2026-10-02T09:15:00", "sku_id": "s1", "store_id": "store_01", "quantity": 2, "unit_price": 395}


def post(client, *rows):
    return client.post("/api/v1/pos/stream", json={"transactions": list(rows)})


def velocity(sku="s1"):
    return {r["hour"]: r["units"] for r in store.list_hourly_velocity(sku_id=sku)}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ingest_batch(client):
    r = post(client, ROW)
    assert r.status_code == 200 and r.json() == {"ingested": 1, "rejected": 0, "errors": []}


def test_ingest_rejects_bad_quantity(client):
    assert post(client, {**ROW, "quantity": 0}).status_code == 422
    assert post(client, {**ROW, "quantity": -3}).status_code == 422


def test_unknown_sku_is_a_clear_error_not_a_db_error(client):
    r = post(client, {**ROW, "sku_id": "nope"})
    body = r.json()
    assert r.status_code == 422 and body["ingested"] == 0 and body["rejected"] == 1
    assert body["errors"] == [{"index": 0, "message": "unknown sku_id 'nope'"}]


def test_unknown_store_rejected(client):
    r = post(client, {**ROW, "store_id": "store_99"})
    assert r.status_code == 422 and "unknown store_id 'store_99'" in r.json()["errors"][0]["message"]


def test_mixed_batch_keeps_good_rows_and_reports_bad_ones(client):
    r = post(client, ROW, {**ROW, "sku_id": "nope"}, {**ROW, "sku_id": "s2"})
    assert r.status_code == 200
    assert (r.json()["ingested"], r.json()["rejected"]) == (2, 1)
    assert r.json()["errors"][0]["index"] == 1
    assert [t for t in store.list_hourly_velocity() if t["sku_id"] == "nope"] == []
    assert velocity("s2") == {datetime(2026, 10, 2, 9): 2}


def test_hourly_velocity_aggregates_per_hour(client):
    post(client, ROW, {**ROW, "timestamp": "2026-10-02T09:50:00", "quantity": 1},
         {**ROW, "timestamp": "2026-10-02T10:05:00", "quantity": 4})
    assert velocity() == {datetime(2026, 10, 2, 9): 3, datetime(2026, 10, 2, 10): 4}


def test_later_batch_for_same_hour_accumulates(client):
    post(client, ROW)
    post(client, {**ROW, "timestamp": "2026-10-02T09:40:00", "quantity": 5})
    assert velocity() == {datetime(2026, 10, 2, 9): 7}


def test_only_affected_hours_are_refreshed(client, backend):
    post(client, ROW, {**ROW, "timestamp": "2026-10-02T10:05:00"})
    before = {k: v for k, v in velocity().items()}
    post(client, {**ROW, "timestamp": "2026-10-02T11:05:00", "quantity": 1})
    after = velocity()
    assert {k: after[k] for k in before} == before and after[datetime(2026, 10, 2, 11)] == 1


def test_timezone_aware_timestamps_become_store_time(client):
    # 03:45Z is 09:15 in Sri Lanka (UTC+5:30)
    post(client, {**ROW, "timestamp": "2026-10-02T03:45:00Z"})
    assert list(velocity()) == [datetime(2026, 10, 2, 9)]


def test_large_batches_are_inserted_in_chunks(client, backend, monkeypatch):
    monkeypatch.setattr(get_settings(), "ingest_chunk_size", 2)
    rows = [{**ROW, "timestamp": f"2026-10-02T09:{m:02d}:00"} for m in range(5)]
    assert post(client, *rows).json()["ingested"] == 5
    if backend is not None:
        assert backend.calls.count(("pos_transactions", "insert")) == 3  # 2 + 2 + 1
    assert velocity() == {datetime(2026, 10, 2, 9): 10}


def test_a_generated_day_ingests_quickly(client, backend):
    df = generate(days=1, end=datetime(2026, 10, 3, 22, 0))
    rows = [{**r, "timestamp": r["timestamp"].isoformat()} for r in df.to_dict("records")]
    t0 = time.perf_counter()
    r = post(client, *rows)
    elapsed = time.perf_counter() - t0
    assert r.json()["ingested"] == len(df) > 1200
    if backend is None:  # the budget is for the in-memory path; the fake has no network to speak of
        assert elapsed < 3


# ---- CSV ---------------------------------------------------------------
def csv(client, text):
    return client.post("/api/v1/pos/stream/csv", content=text, headers={"Content-Type": "text/csv"})


def test_csv_ingest(client):
    r = csv(client, "timestamp,sku_id,store_id,quantity,unit_price\n"
                    "2026-10-02T09:15:00,s1,store_01,2,395\n2026-10-02T09:20:00,s1,store_01,1,395\n")
    assert r.status_code == 200 and r.json()["ingested"] == 2
    assert velocity() == {datetime(2026, 10, 2, 9): 3}


def test_csv_store_id_is_optional(client):
    r = csv(client, "timestamp,sku_id,quantity,unit_price\n2026-10-02T09:15:00,s1,2,395\n")
    assert r.json()["ingested"] == 1


def test_csv_reports_bad_rows_by_index(client):
    r = csv(client, "timestamp,sku_id,quantity,unit_price\n"
                    "2026-10-02T09:15:00,s1,2,395\nnot-a-date,s1,2,395\n2026-10-02T09:15:00,zzz,1,395\n"
                    "2026-10-02T09:15:00,s1,0,395\n")
    body = r.json()
    assert r.status_code == 200 and body["ingested"] == 1 and body["rejected"] == 3
    assert [e["index"] for e in body["errors"]] == [1, 2, 3]


def test_csv_missing_column_is_422(client):
    r = csv(client, "timestamp,sku_id\n2026-10-02T09:15:00,s1\n")
    assert r.status_code == 422 and "quantity" in r.json()["detail"]


def test_csv_round_trips_the_generator_output(client, tmp_path):
    df = generate(days=1, end=datetime(2026, 10, 3, 12, 0))
    path = tmp_path / "day.csv"
    df.to_csv(path, index=False)
    r = csv(client, path.read_text())
    assert r.json() == {"ingested": len(df), "rejected": 0, "errors": []}
