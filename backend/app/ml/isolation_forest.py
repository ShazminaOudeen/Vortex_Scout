"""Isolation Forest & blended anomaly scorer (Feature B4).

Extracts multi-dimensional features per SKU:
  1. silent_hours: trailing run of zero-sale open hours (zero streak)
  2. expected_sales: missed sales during the silence (from ZIP/baseline)
  3. history_rate: normal sales velocity per open hour
  4. silence_exposure_ratio: trading exposure of silence vs history
  5. hours_since_last_sale: elapsed gap in hours

Blends the Isolation Forest outlier score with the statistical posterior (B1/B3)
to produce a robust final p_void in [0, 1].
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.ml.baseline import (
    DISPERSION,
    MAX_EVIDENCE_HOURS,
    MIN_HISTORY_HOURS,
    MIN_SILENT_HOURS,
    PRIOR_VOID,
    OUTPUT_COLUMNS,
)
from app.ml.feature_pipeline import add_time_features
from app.ml.zip_model import ZipBaseline, score_voids as zip_score_voids

BLEND_ALPHA = 0.70  # 70% statistical posterior (B1/B3), 30% Isolation Forest outlier score


def extract_features(
    velocity: pd.DataFrame,
    zip_model: ZipBaseline | None = None,
    max_evidence_hours: int = MAX_EVIDENCE_HOURS,
) -> pd.DataFrame:
    """Build multi-dimensional feature rows per SKU from the dense velocity frame."""
    if velocity.empty:
        return pd.DataFrame(columns=[
            "sku_id", "silent_hours", "expected_sales", "history_rate",
            "silence_exposure_ratio", "hours_since_last_sale", "n_hist"
        ])

    v = add_time_features(velocity.copy()).sort_values(["sku_id", "hour"]).reset_index(drop=True)
    v["slot"] = (v["day_of_week"] >= 5).astype(int) * 24 + v["hour_of_day"]

    sold = v["units"] > 0
    cum_sales = sold.groupby(v["sku_id"]).cumsum()
    total_sales = cum_sales.groupby(v["sku_id"]).transform("max")
    v["trailing"] = (cum_sales == total_sales) & ~sold

    hist = v[~v["trailing"]]
    overall_mean = hist["units"].mean() if not hist.empty else 1.0
    overall_mean = overall_mean if overall_mean > 0 else 1.0
    slot_profile = (hist.groupby("slot")["units"].mean() / overall_mean).reindex(range(48)).fillna(1.0)
    v["profile"] = v["slot"].map(slot_profile)
    hist = v[~v["trailing"]]

    # Historical metrics per SKU
    g_hist = hist.groupby("sku_id")
    units_hist = g_hist["units"].sum().rename("units_hist")
    n_hist = g_hist.size().rename("n_hist")
    p_hist = g_hist["profile"].sum().rename("p_hist")

    tail = v[v["trailing"]]
    recent = tail[tail.groupby("sku_id").cumcount(ascending=False) < max_evidence_hours]
    p_silent = recent.groupby("sku_id")["profile"].sum().rename("p_silent")
    silent_hours = tail.groupby("sku_id").size().rename("silent_hours")

    # Fit or use ZIP baseline for expected sales
    if zip_model is None:
        zip_model = ZipBaseline().fit(v)

    records = []
    all_skus = v["sku_id"].unique()
    for sku_id in all_skus:
        n_h = int(n_hist.get(sku_id, 0))
        u_h = float(units_hist.get(sku_id, 0.0))
        p_h = float(p_hist.get(sku_id, 0.0))
        s_hrs = int(silent_hours.get(sku_id, 0))
        p_sil = float(p_silent.get(sku_id, 0.0))

        hist_rate = u_h / max(n_h, 1)
        exposure_ratio = p_sil / max(p_h, 1e-3)

        # Expected sales from ZIP model
        sku_recent = recent[recent["sku_id"] == sku_id]
        exp_sales = sum(zip_model.expected_rate(sku_id, pd.Timestamp(h)) for h in sku_recent["hour"]) if s_hrs > 0 else 0.0

        records.append({
            "sku_id": sku_id,
            "silent_hours": s_hrs,
            "expected_sales": round(exp_sales, 2),
            "history_rate": round(hist_rate, 3),
            "silence_exposure_ratio": round(exposure_ratio, 3),
            "hours_since_last_sale": float(s_hrs),
            "n_hist": n_h,
        })

    return pd.DataFrame(records)


def score_voids(
    velocity: pd.DataFrame,
    zip_model: ZipBaseline | None = None,
    alpha: float = BLEND_ALPHA,
    prior: float = PRIOR_VOID,
    min_silent_hours: int = MIN_SILENT_HOURS,
    min_history_hours: int = MIN_HISTORY_HOURS,
    dispersion: float = DISPERSION,
    random_state: int = 42,
) -> pd.DataFrame:
    """Anomaly scorer: combine ZIP probabilities with Isolation Forest.

    Returns DataFrame: [sku_id, silent_hours, expected_sales, p_void, hours_since_last_sale].
    """
    if velocity.empty:
        cols = list(OUTPUT_COLUMNS) + ["hours_since_last_sale"]
        return pd.DataFrame({c: pd.Series(dtype="float64" if c != "sku_id" else "object") for c in cols})

    feat = extract_features(velocity, zip_model=zip_model)
    if zip_model is None:
        zip_model = ZipBaseline(dispersion=dispersion).fit(velocity)

    # Base statistical score from ZIP
    zip_scores = zip_score_voids(
        velocity,
        zip_model=zip_model,
        prior=prior,
        min_silent_hours=min_silent_hours,
        min_history_hours=min_history_hours,
        dispersion=dispersion,
    ).set_index("sku_id")

    feat = feat.set_index("sku_id")
    feature_cols = ["silent_hours", "expected_sales", "history_rate", "silence_exposure_ratio"]
    X = feat[feature_cols].to_numpy(dtype=float)

    # Fit Isolation Forest
    iso = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=random_state,
        n_jobs=1,
    )
    iso.fit(X)

    # Decision function: negative values indicate outliers
    scores = iso.decision_function(X)
    s_min, s_max = float(scores.min()), float(scores.max())
    span = (s_max - s_min) if (s_max - s_min) > 1e-6 else 1.0
    iso_p = 1.0 - ((scores - s_min) / span)

    out_records = []
    for idx, sku_id in enumerate(feat.index):
        row = feat.loc[sku_id]
        stat_p = float(zip_scores.loc[sku_id, "p_void"]) if sku_id in zip_scores.index else 0.0
        exp_sales = float(zip_scores.loc[sku_id, "expected_sales"]) if sku_id in zip_scores.index else 0.0
        silent_h = int(row["silent_hours"])
        n_h = int(row["n_hist"])

        eligible = (silent_h >= min_silent_hours) and (n_h >= min_history_hours)
        if eligible:
            blended = alpha * stat_p + (1.0 - alpha) * iso_p[idx]
            if stat_p >= 0.70:
                final_p = max(stat_p, blended)
            else:
                final_p = blended
        else:
            final_p = 0.0

        out_records.append({
            "sku_id": sku_id,
            "silent_hours": silent_h,
            "expected_sales": round(exp_sales, 2),
            "p_void": round(float(np.clip(final_p, 0.0, 1.0)), 3),
            "hours_since_last_sale": float(row["hours_since_last_sale"]),
        })

    cols = ["sku_id", "silent_hours", "expected_sales", "p_void", "hours_since_last_sale"]
    return pd.DataFrame(out_records)[cols]
