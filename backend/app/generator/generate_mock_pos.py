"""Synthetic POS generator.

Usage (from backend/):
    python -m app.generator.generate_mock_pos --days 14 --phantom s1 --out mock_pos.csv
    python -m app.generator.generate_mock_pos --days 14 --phantom s1 --scenario backroom_stuck

Shape of the data
  * 200 SKUs (mock_skus.json); each has a `base_rate` = expected sale lines per open hour.
  * Store is open 08:00-22:00. Peak hours 11-13 and 18-21 sell at 2x.
  * Weekends sell 1.2x, payday days (PAYDAY_DAYS) 1.12x.
  * ~1,330 lines on a plain weekday, ~1,790 on a weekend payday: always inside 1,200-2,000.
  * One row per sale line: [timestamp, sku_id, store_id, quantity, unit_price].

Phantom scenarios (the SKU's ledger stays high while the shelf is empty):
  frozen          abrupt stop - stock misplaced / stuck somewhere else
  damaged         abrupt stop - shelf contents spoiled or pulled; needs a ledger write-off
  backroom_stuck  sales taper off over ~3 hours as the shelf drains, replenishment never arrives
"""
import argparse
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from app.generator.catalog import load_catalog
from app.ml.feature_pipeline import CLOSE_HOUR, OPEN_HOUR, PEAK_HOURS

WEEKEND_FACTOR = 1.2
PAYDAY_FACTOR = 1.12
PAYDAY_DAYS = {1, 2, 25, 26, 27}

SCENARIOS = {
    "frozen": {"description": "Sales stop abruptly while the ledger stays high.", "expected_action": "restocked"},
    "damaged": {"description": "Shelf stock spoiled or pulled; sales stop, ledger needs a write-off.",
                "expected_action": "damaged"},
    "backroom_stuck": {"description": "Stock stuck in the backroom; the shelf drains and sales taper to zero.",
                       "expected_action": "restocked"},
}
TAPER_HOURS = 3  # backroom_stuck: sales fully stop from the 4th hour of the window


def _hour_factor(ts: datetime, force_peak: bool = False) -> float:
    if not OPEN_HOUR <= ts.hour < CLOSE_HOUR:  # store closed
        return 0.0
    f = 2.0 if (force_peak or ts.hour in PEAK_HOURS) else 1.0
    if ts.weekday() >= 5:
        f *= WEEKEND_FACTOR
    if ts.day in PAYDAY_DAYS:
        f *= PAYDAY_FACTOR
    return f


def _phantom_multiplier(scenario: str, hours_in: int) -> float:
    """Share of normal sales that still happens `hours_in` hours after the freeze starts."""
    if scenario == "backroom_stuck":
        return max(0.0, 1 - (hours_in + 1) / (TAPER_HOURS + 1))
    return 0.0


def generate_hours(hours: list[datetime], phantom_sku: str | None = None, scenario: str = "frozen",
                   phantom_from: datetime | None = None, store_id: str = "store_01", seed: int = 42,
                   force_peak: bool = False) -> pd.DataFrame:
    """Sales for an explicit list of hour starts (need not be contiguous).

    The phantom SKU follows `scenario` for every hour >= `phantom_from`.
    `force_peak` makes every hour sell at peak intensity (the demo's "normal peak" button).
    """
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}; choose from {sorted(SCENARIOS)}")
    rng = np.random.default_rng(seed)
    skus = load_catalog()
    ids = [s["id"] for s in skus]
    base = np.array([s["base_rate"] for s in skus])
    prices = {s["id"]: s["unit_price"] for s in skus}
    phantom_idx = ids.index(phantom_sku) if phantom_sku in ids else None

    rows = []
    for h in sorted(hours):
        factor = _hour_factor(h, force_peak)
        if not factor:
            continue
        lam = base * factor
        if phantom_idx is not None and phantom_from is not None and h >= phantom_from:
            hours_in = int((h - phantom_from).total_seconds() // 3600)
            lam[phantom_idx] *= _phantom_multiplier(scenario, hours_in)
        counts = rng.poisson(lam)
        for i in np.flatnonzero(counts):
            for _ in range(counts[i]):
                rows.append({
                    "timestamp": h + timedelta(minutes=int(rng.integers(0, 60)), seconds=int(rng.integers(0, 60))),
                    "sku_id": ids[i], "store_id": store_id,
                    "quantity": int(rng.integers(1, 3)), "unit_price": prices[ids[i]],
                })
    df = pd.DataFrame(rows, columns=["timestamp", "sku_id", "store_id", "quantity", "unit_price"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df.attrs["scenario"] = scenario if phantom_idx is not None else None
    df.attrs["expected_action"] = SCENARIOS[scenario]["expected_action"] if phantom_idx is not None else None
    return df


def generate(days: int = 14, phantom_sku: str | None = None,
             phantom_hours: int = 10, store_id: str = "store_01",
             seed: int = 42, end: datetime | None = None,
             scenario: str = "frozen", phantom_from: datetime | None = None) -> pd.DataFrame:
    """`days` of history ending (exclusive) at `end`.

    The phantom SKU misbehaves from `phantom_from` (default: `end - phantom_hours`) to the end,
    while its ledger stock stays positive (the shelf is empty).
    """
    end = end or datetime.now().replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days)
    if phantom_from is None:
        phantom_from = end - timedelta(hours=phantom_hours)
    hours = [start + timedelta(hours=i) for i in range(int((end - start).total_seconds() // 3600))]
    return generate_hours(hours, phantom_sku, scenario, phantom_from, store_id, seed)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--phantom", default=None, help="sku id to freeze, e.g. s1")
    p.add_argument("--scenario", default="frozen", choices=sorted(SCENARIOS))
    p.add_argument("--phantom-hours", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default="mock_pos.csv")
    a = p.parse_args()
    df = generate(a.days, a.phantom, a.phantom_hours, seed=a.seed, scenario=a.scenario)
    df.to_csv(a.out, index=False)
    print(f"Wrote {len(df)} rows to {a.out}")
