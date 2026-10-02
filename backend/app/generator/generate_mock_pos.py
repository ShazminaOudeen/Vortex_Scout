"""Synthetic POS generator (starter version).

Usage (from backend/):
    python -m app.generator.generate_mock_pos --days 14 --phantom s1 --out mock_pos.csv

TODO(Task 1): scale to 200 SKUs, add weekday/weekend + payday effects,
and support several phantom scenarios (damaged, dumped, backroom stuck).
"""
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SKUS_PATH = Path(__file__).with_name("mock_skus.json")
PEAK_HOURS = {11, 12, 18, 19, 20}


def _hour_factor(ts: datetime) -> float:
    if not 8 <= ts.hour < 22:  # store closed
        return 0.0
    f = 2.0 if ts.hour in PEAK_HOURS else 1.0
    return f * (1.4 if ts.weekday() >= 5 else 1.0)


def generate(days: int = 14, phantom_sku: str | None = None,
             phantom_hours: int = 10, store_id: str = "store_01",
             seed: int = 42, end: datetime | None = None) -> pd.DataFrame:
    """One row per sale. The phantom SKU stops selling for the last `phantom_hours`
    hours while its ledger stock stays positive (the shelf is empty)."""
    rng = np.random.default_rng(seed)
    skus = json.loads(SKUS_PATH.read_text())
    end = end or datetime.now().replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days)
    freeze_from = end - timedelta(hours=phantom_hours)

    rows = []
    ts = start
    while ts < end:
        factor = _hour_factor(ts)
        for s in skus:
            if s["id"] == phantom_sku and ts >= freeze_from:
                continue
            n = rng.poisson(s["base_rate"] * factor) if factor else 0
            for _ in range(n):
                rows.append({
                    "timestamp": ts + timedelta(minutes=int(rng.integers(0, 60))),
                    "sku_id": s["id"], "store_id": store_id,
                    "quantity": int(rng.integers(1, 3)), "unit_price": s["unit_price"],
                })
        ts += timedelta(hours=1)
    return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--phantom", default=None, help="sku id to freeze, e.g. s1")
    p.add_argument("--out", default="mock_pos.csv")
    a = p.parse_args()
    df = generate(a.days, a.phantom)
    df.to_csv(a.out, index=False)
    print(f"Wrote {len(df)} rows to {a.out}")
