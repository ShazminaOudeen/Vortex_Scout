"""Run shelf-void detection end to end.

    feature store (get_velocity) -> baseline scorer (app.ml.baseline) -> open / refresh / clear anomalies

The detector is the source of truth for open anomalies: after a run, the open anomalies are exactly the
SKUs it currently flags. A SKU that is still flagged keeps its anomaly (numbers refreshed, same id and
detected_at); a newly flagged SKU gets a new one; an open anomaly whose SKU is no longer flagged is
removed. Anomalies a supervisor already resolved are never touched.

Alert rule (from the project spec): p_void >= settings.void_threshold AND ledger stock > 0. If the
ledger already shows zero, the system already knows the product is out, so it is not a phantom.

Known limitation: after a supervisor taps "Restocked", re-running detection on *unchanged* sales data
flags the SKU again, because nothing in the data says the shelf was refilled. In real operation sales
resume and the alert disappears; in the demo, push "Simulate Normal Peak" before running detection again.
"""
import pandas as pd

from app.core import store
from app.core.config import get_settings
from app.ml.baseline import score_voids
from app.ml.feature_pipeline import get_velocity, hours_since_last_sale


def run_detection() -> dict:
    thr = get_settings().void_threshold
    velocity = get_velocity()
    if velocity.empty:
        return {"flagged": 0, "created": 0, "updated": 0, "cleared": 0, "threshold": thr, "data_as_of": None,
                "alerts": [], "note": "No sales data yet; nothing was changed. Ingest POS data or run a simulation first."}

    scores = score_voids(velocity)
    gap = hours_since_last_sale().set_index("sku_id")["hours_since_last_sale"]
    skus = {s.id: s for s in store.list_skus()}

    candidates = scores[scores["p_void"] >= thr].sort_values("p_void", ascending=False)
    flagged, ledger_zero = [], 0
    for r in candidates.itertuples():
        sku = skus.get(r.sku_id)
        if sku is None:
            continue
        if sku.ledger_stock <= 0:
            ledger_zero += 1
            continue
        flagged.append((r, sku))

    # Sync open anomalies with what the detector supports now.
    open_by_sku: dict[str, str] = {}
    duplicates: list[str] = []  # a SKU should have one open anomaly; extras are removed
    for a in sorted(store.list_anomalies(status="open"), key=lambda x: x.detected_at):
        if a.sku_id in open_by_sku:
            duplicates.append(a.id)
        else:
            open_by_sku[a.sku_id] = a.id

    created = updated = 0
    alerts = []
    keep = set()
    for r, sku in flagged:
        hours = float(gap.get(r.sku_id, r.silent_hours))
        existing = open_by_sku.get(r.sku_id)
        if existing and store.update_anomaly(existing, r.p_void, hours, sku.ledger_stock):
            updated += 1
        else:
            store.create_anomaly(r.sku_id, r.p_void, hours, ledger_stock=sku.ledger_stock)
            created += 1
        keep.add(r.sku_id)
        alerts.append({"sku_id": r.sku_id, "sku_name": sku.name, "aisle": sku.aisle, "bay": sku.bay,
                       "p_void": float(r.p_void), "silent_hours": int(r.silent_hours),
                       "expected_sales": float(r.expected_sales), "ledger_stock": sku.ledger_stock})

    cleared = 0
    for sku_id, anomaly_id in open_by_sku.items():
        if sku_id not in keep and store.delete_anomaly(anomaly_id):
            cleared += 1
    cleared += sum(store.delete_anomaly(a_id) for a_id in duplicates)

    return {"flagged": len(flagged), "created": created, "updated": updated, "cleared": cleared,
            "ledger_zero_skipped": ledger_zero, "threshold": thr,
            "data_as_of": (pd.Timestamp(velocity["hour"].max()) + pd.Timedelta(hours=1)).isoformat(),
            "alerts": alerts}
