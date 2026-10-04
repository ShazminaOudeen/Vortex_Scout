from datetime import datetime

import pytest

from app.core import store
from app.generator import seed as seed_mod
from app.generator.generate_mock_pos import generate
from app.generator.load_csv import load
from app.ml.feature_pipeline import get_velocity

END = datetime(2026, 10, 3, 22, 0)


def snapshot():
    v = get_velocity()
    return (len(store.list_hourly_velocity()), int(v.units.sum()),
            tuple(sorted(s.ledger_stock for s in store.list_skus())), len(store.list_anomalies()))


def test_seed_refuses_to_run_without_supabase(backend):
    if backend is not None:
        pytest.skip("only meaningful on the in-memory backend")
    with pytest.raises(RuntimeError, match="not configured"):
        seed_mod.seed(days=1, end=END)
    assert seed_mod.main(["--yes"]) == 1


def test_seed_is_idempotent(backend):
    if backend is None:
        pytest.skip("seed needs a Supabase client (the fake stands in for it)")
    first = seed_mod.seed(days=2, phantom="s1", end=END)
    state1 = snapshot()
    store.set_ledger_stock("s1", 5)           # drift the demo state...
    second = seed_mod.seed(days=2, phantom="s1", end=END)
    assert snapshot() == state1               # ...and re-running restores it exactly
    assert first["ingested"] == second["ingested"] == len(generate(days=2, phantom_sku="s1", end=END))
    assert first["rejected"] == 0 and first["skus"] == 200
    assert store.get_sku("s1").ledger_stock == 70
    assert len(backend.tables["pos_transactions"]) == first["ingested"]  # no duplicate rows after the re-run


def test_seed_loads_one_day_per_ingest_call(backend):
    if backend is None:
        pytest.skip("needs the fake client's call log")
    seed_mod.seed(days=3, end=END)
    # reset() deletes once; the 3 daily batches each insert at least once
    assert backend.calls.count(("pos_transactions", "insert")) >= 3


def test_csv_loader_chunks_and_reports_file_level_row_numbers(client, tmp_path):
    df = generate(days=1, end=datetime(2026, 10, 3, 14, 0))
    df.loc[5, "sku_id"] = "bogus"
    path = tmp_path / "day.csv"
    df.to_csv(path, index=False)

    posts = []

    def post(text):
        posts.append(text)
        r = client.post("/api/v1/pos/stream/csv", content=text, headers={"Content-Type": "text/csv"})
        return r.json()

    result = load(path, post, rows_per_chunk=400)
    assert len(posts) == -(-len(df) // 400) > 1                 # several requests
    assert all(t.startswith("timestamp,") for t in posts)       # header repeated in each chunk
    assert result["ingested"] == len(df) - 1 and result["rejected"] == 1
    assert result["errors"][0]["index"] == 5 and "bogus" in result["errors"][0]["message"]
