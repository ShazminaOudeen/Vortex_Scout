"""Judge-demo scenarios (used by /api/v1/simulate). They generate traffic with the same generator
as the history and push it through the real ingest path (app.services.ingest)."""
from datetime import datetime, timedelta

from app.core import store
from app.core.timeutil import floor_hour, store_now
from app.generator.generate_mock_pos import SCENARIOS, generate, generate_hours
from app.ml.feature_pipeline import CLOSE_HOUR, OPEN_HOUR
from app.services.ingest import ingest

PHANTOM_SKU = "s1"          # Munchee Super Cream Cracker 490g
PHANTOM_LEDGER = 40         # units the ERP still believes are on hand
PHANTOM_HOURS = 8           # open hours with zero sales
NORMAL_HOURS = 3            # open hours of peak-intensity traffic
BASELINE_DAYS = 7           # history created when the store is empty


def _is_open(h: datetime) -> bool:
    return OPEN_HOUR <= h.hour < CLOSE_HOUR


def open_hours_after(latest: datetime, n: int) -> list[datetime]:
    """The next `n` trading hours strictly after `latest` (the demo stream continues the data clock)."""
    out, h = [], latest
    while len(out) < n:
        h += timedelta(hours=1)
        if _is_open(h):
            out.append(h)
    return out


def recent_open_hours(n: int, now: datetime | None = None) -> list[datetime]:
    """The `n` most recent *completed* trading hours before `now` (oldest first)."""
    h, out = floor_hour(now or store_now()), []
    while len(out) < n:
        h -= timedelta(hours=1)
        if _is_open(h):
            out.append(h)
    return out[::-1]


def inject_phantom(variant: str = "frozen", sku_id: str = PHANTOM_SKU) -> dict:
    """The phantom stockout: `sku_id` shows zero (or tapering) sales for PHANTOM_HOURS open hours
    while the ledger says PHANTOM_LEDGER units. Appends to existing history; if the store is empty
    a week of baseline history is created first."""
    if variant not in SCENARIOS:
        raise ValueError(f"unknown variant {variant!r}")
    latest = store.latest_velocity_hour()
    if latest is None:
        window = recent_open_hours(PHANTOM_HOURS)
        end = window[-1] + timedelta(hours=1)
        df = generate(days=BASELINE_DAYS, phantom_sku=sku_id, scenario=variant, phantom_from=window[0], end=end,
                      seed=int(end.timestamp()) % 2**32)
    else:
        window = open_hours_after(latest, PHANTOM_HOURS)
        df = generate_hours(window, phantom_sku=sku_id, scenario=variant, phantom_from=window[0],
                            seed=int(latest.timestamp()) % 2**32)
    result = ingest(df.to_dict("records"))
    store.set_ledger_stock(sku_id, PHANTOM_LEDGER)
    return {"sku_id": sku_id, "variant": variant, "expected_action": SCENARIOS[variant]["expected_action"],
            "ledger_stock": PHANTOM_LEDGER, "silent_hours": PHANTOM_HOURS,
            "window_start": window[0].isoformat(), "window_end": (window[-1] + timedelta(hours=1)).isoformat(),
            "ingested": result.ingested, "rejected": result.rejected}


def inject_normal() -> dict:
    """Healthy peak-hour traffic across every SKU, continuing the data clock."""
    latest = store.latest_velocity_hour()
    if latest is None:
        window = recent_open_hours(NORMAL_HOURS)
        end = window[-1] + timedelta(hours=1)
        df = generate(days=BASELINE_DAYS, end=end, seed=int(end.timestamp()) % 2**32)
    else:
        window = open_hours_after(latest, NORMAL_HOURS)
        df = generate_hours(window, seed=int(latest.timestamp()) % 2**32, force_peak=True)
    result = ingest(df.to_dict("records"))
    return {"hours": NORMAL_HOURS, "window_start": window[0].isoformat(),
            "window_end": (window[-1] + timedelta(hours=1)).isoformat(),
            "ingested": result.ingested, "rejected": result.rejected}
