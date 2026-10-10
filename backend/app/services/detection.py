"""Run shelf-void detection end to end with adaptive threshold calibration (Feature B5).

    feature store (get_velocity) -> ML scorer -> open / refresh / clear anomalies

The detector is the source of truth for open anomalies: after a run, the open anomalies are exactly the
SKUs it currently flags. A SKU that is still flagged keeps its anomaly (numbers refreshed, same id and
detected_at); a newly flagged SKU gets a new one; an open anomaly whose SKU is no longer flagged is
removed. Anomalies a supervisor already resolved are never touched.

Feature B5: Threshold Calibration:
    Automatically adjusts void_threshold based on the live false_alarm_rate from store.audit_action_counts().
    High false alarms (> 15%) raise the threshold to reduce alert fatigue. Low false alarms with good volume
    allow slightly more sensitive detection.
"""
from __future__ import annotations

import pandas as pd

from app.core import store
from app.core.config import get_settings
from app.ml.baseline import score_voids
from app.ml.feature_pipeline import get_velocity, hours_since_last_sale

MIN_CALIBRATION_AUDITS = 5


def calibrate_threshold(base_threshold: float | None = None, min_audits: int = MIN_CALIBRATION_AUDITS) -> tuple[float, dict]:
    """Calculate the effective void threshold tuned by historical audit accuracy (Feature B5).

    Returns (effective_threshold, calibration_metadata).
    """
    if base_threshold is None:
        base_threshold = get_settings().void_threshold

    counts = store.audit_action_counts()
    total = sum(counts.values())
    false_alarms = counts.get("false_alarm", 0)

    if total < min_audits:
        return float(base_threshold), {
            "base_threshold": base_threshold,
            "effective_threshold": base_threshold,
            "total_audits": total,
            "false_alarm_rate": 0.0,
            "status": "default",
            "reason": f"Insufficient audit logs ({total}/{min_audits}); using base threshold.",
        }

    false_alarm_rate = false_alarms / total

    # Threshold calibration rules
    if false_alarm_rate > 0.20:
        # Severe alert fatigue: increase threshold significantly
        effective = min(0.90, base_threshold + 0.10)
        status = "conservative_high"
        reason = f"High false alarm rate ({false_alarm_rate:.1%}); increased threshold to reduce alert fatigue."
    elif false_alarm_rate > 0.10:
        # Moderate false alarms: slight increase
        effective = min(0.85, base_threshold + 0.05)
        status = "conservative"
        reason = f"Elevated false alarm rate ({false_alarm_rate:.1%}); adjusted threshold slightly."
    elif false_alarm_rate < 0.05 and total >= 10:
        # High precision & trusted volume: can afford more sensitive detection
        effective = max(0.65, base_threshold - 0.05)
        status = "sensitive"
        reason = f"Low false alarm rate ({false_alarm_rate:.1%}); tuned threshold for higher sensitivity."
    else:
        effective = base_threshold
        status = "optimal"
        reason = f"False alarm rate ({false_alarm_rate:.1%}) within acceptable bounds."

    effective = round(float(effective), 2)
    return effective, {
        "base_threshold": base_threshold,
        "effective_threshold": effective,
        "total_audits": total,
        "false_alarm_rate": round(false_alarm_rate, 4),
        "status": status,
        "reason": reason,
    }


def get_threshold_status() -> dict:
    """Read current threshold status without executing detection."""
    effective, meta = calibrate_threshold()
    return meta


def run_detection(threshold_override: float | None = None) -> dict:
    effective_thr, calibration_info = calibrate_threshold()
    thr = threshold_override if threshold_override is not None else effective_thr

    velocity = get_velocity()
    if velocity.empty:
        return {
            "flagged": 0, "created": 0, "updated": 0, "cleared": 0, "threshold": thr,
            "calibration": calibration_info, "data_as_of": None, "alerts": [],
            "note": "No sales data yet; nothing was changed. Ingest POS data or run a simulation first."
        }

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
    duplicates: list[str] = []
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
        alerts.append({
            "sku_id": r.sku_id, "sku_name": sku.name, "aisle": sku.aisle, "bay": sku.bay,
            "p_void": float(r.p_void), "silent_hours": int(r.silent_hours),
            "expected_sales": float(r.expected_sales), "ledger_stock": sku.ledger_stock
        })

    cleared = 0
    for sku_id, anomaly_id in open_by_sku.items():
        if sku_id not in keep and store.delete_anomaly(anomaly_id):
            cleared += 1
    cleared += sum(store.delete_anomaly(a_id) for a_id in duplicates)

    return {
        "flagged": len(flagged), "created": created, "updated": updated, "cleared": cleared,
        "ledger_zero_skipped": ledger_zero, "threshold": thr, "calibration": calibration_info,
        "data_as_of": (pd.Timestamp(velocity["hour"].max()) + pd.Timedelta(hours=1)).isoformat(),
        "alerts": alerts
    }
