"""Load the demo store, the 200-SKU catalog and N days of synthetic POS history into Supabase.

    python -m app.generator.seed                      # 14 days of normal trading, asks before wiping
    python -m app.generator.seed --phantom s1 --scenario frozen --yes

Idempotent: it first resets the demo tables (transactions, hourly_velocity, anomalies, audit_log),
restores stores/SKUs (ledger stock included) from mock_skus.json, then loads the history one day at
a time through the normal ingest path, so re-running always ends in the same state. Needs
SUPABASE_URL and SUPABASE_KEY in backend/.env (run supabase/schema.sql first).
"""
import argparse
import sys
import time
from datetime import datetime

from app.core import store
from app.core.timeutil import floor_hour, store_now
from app.generator.generate_mock_pos import SCENARIOS, generate
from app.services.ingest import ingest


def seed(days: int = 14, phantom: str | None = None, scenario: str = "frozen", phantom_hours: int = 10,
         seed_value: int = 42, end: datetime | None = None) -> dict:
    if not store.using_supabase():
        raise RuntimeError("Supabase is not configured: set SUPABASE_URL and SUPABASE_KEY in backend/.env")
    t0 = time.perf_counter()
    store.reset()
    end = end or floor_hour(store_now())
    df = generate(days=days, phantom_sku=phantom, phantom_hours=phantom_hours, scenario=scenario,
                  seed=seed_value, end=end)
    ingested = rejected = 0
    for _, day in df.groupby(df["timestamp"].dt.date):
        result = ingest(day.to_dict("records"))
        ingested += result.ingested
        rejected += result.rejected
    return {"days": days, "rows": len(df), "ingested": ingested, "rejected": rejected,
            "skus": len(store.list_skus()), "phantom": phantom, "end": end.isoformat(),
            "seconds": round(time.perf_counter() - t0, 1)}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--phantom", default=None, help="sku id to freeze at the end of the history, e.g. s1")
    p.add_argument("--scenario", default="frozen", choices=sorted(SCENARIOS))
    p.add_argument("--phantom-hours", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    a = p.parse_args(argv)
    if not store.using_supabase():
        print("Supabase is not configured: set SUPABASE_URL and SUPABASE_KEY in backend/.env", file=sys.stderr)
        return 1
    if not a.yes and input("This DELETES all rows in pos_transactions, hourly_velocity, stockout_anomalies "
                           "and audit_log, then reloads the demo data. Continue? [y/N] ").lower() != "y":
        print("Aborted.")
        return 1
    print(seed(a.days, a.phantom, a.scenario, a.phantom_hours, a.seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
