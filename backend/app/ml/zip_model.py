"""Zero-Inflated Poisson (ZIP) baseline for shelf-void detection (Feature B3).

Models hourly sales count data as a mixture of:
  1. A structural zero probability pi (off-peak, slow seller, nobody bought it)
  2. A Poisson count distribution with rate lambda (when product is in active consideration)

Total probability of observing zero sales in hour t:
    P(Y = 0) = pi + (1 - pi) * exp(-lambda)
Expected sales rate:
    E[Y] = (1 - pi) * lambda

For a run of silent hours, the likelihood of the silence under normal trading is:
    L(silence) = Prod P(Y_t = 0)
    Evidence E = -Sum ln P(Y_t = 0)
    p_void = logistic(E / dispersion + logit(prior))

This naturally dampens suspicion for slow-sellers and off-peak periods, preventing
alert fatigue while catching fast movers that abruptly freeze.
"""
from __future__ import annotations

import warnings
import numpy as np
import pandas as pd
from statsmodels.discrete.count_model import ZeroInflatedPoisson

from app.ml.baseline import (
    DISPERSION,
    MAX_EVIDENCE_HOURS,
    MIN_HISTORY_HOURS,
    MIN_SILENT_HOURS,
    OUTPUT_COLUMNS,
    PRIOR_VOID,
    _logistic,
)
from app.ml.feature_pipeline import add_time_features


class ZipBaseline:
    """Per-SKU Zero-Inflated Poisson estimator with time-of-day features."""

    def __init__(self, dispersion: float = DISPERSION):
        self.dispersion = dispersion
        self.sku_params: dict[str, dict[str, float]] = {}
        self.slot_profile: dict[int, float] = {}
        self.overall_mean: float = 0.0

    def fit(self, velocity: pd.DataFrame) -> "ZipBaseline":
        """Fit ZIP parameters on dense velocity data (with explicit zero hours)."""
        if velocity.empty:
            return self

        v = add_time_features(velocity.copy())
        # 48 trading slots: weekday/weekend (0/1) * 24 + hour_of_day
        v["slot"] = (v["day_of_week"] >= 5).astype(int) * 24 + v["hour_of_day"]

        # Only use history before trailing zeros for fitting
        sold = v["units"] > 0
        cum_sales = sold.groupby(v["sku_id"]).cumsum()
        total_sales = cum_sales.groupby(v["sku_id"]).transform("max")
        v["trailing"] = (cum_sales == total_sales) & ~sold

        hist = v[~v["trailing"]]
        self.overall_mean = float(hist["units"].mean()) if not hist.empty else 0.0

        if self.overall_mean <= 0:
            return self

        # Store-wide trading rhythm
        slot_means = hist.groupby("slot")["units"].mean() / self.overall_mean
        self.slot_profile = slot_means.reindex(range(48)).fillna(1.0).to_dict()

        for sku_id, group in hist.groupby("sku_id"):
            n_obs = len(group)
            if n_obs < MIN_HISTORY_HOURS or group["units"].sum() == 0:
                self.sku_params[sku_id] = {"pi": 0.95, "lambda_base": 0.05, "fitted": False}
                continue

            y = group["units"].to_numpy(dtype=float)
            zero_fraction = float(np.mean(y == 0))
            mean_y = float(np.mean(y))

            # Attempt statsmodels ZeroInflatedPoisson if enough data and variation
            fitted = False
            if n_obs >= 30 and zero_fraction > 0.05 and zero_fraction < 0.98 and np.var(y) > 0.01:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        X = np.column_stack([np.ones(n_obs), group["is_peak"].to_numpy(dtype=float)])
                        model = ZeroInflatedPoisson(endog=y, exog=X, exog_infl=X, inflation="logit")
                        res = model.fit(disp=False, maxiter=35)
                        pred_pi = float(res.predict(exog=[[1.0, 0.0]], exog_infl=[[1.0, 0.0]], which="prob-zero")[0])
                        pred_rate = float(res.predict(exog=[[1.0, 0.0]], which="mean")[0])
                        self.sku_params[sku_id] = {
                            "pi": np.clip(pred_pi, 0.01, 0.99),
                            "lambda_base": max(0.01, pred_rate),
                            "fitted": True,
                        }
                        fitted = True
                except Exception:
                    fitted = False

            if not fitted:
                # Robust empirical moment estimation:
                # E[Y] = (1 - pi) * lambda, P(Y=0) = pi + (1 - pi) * exp(-lambda)
                if zero_fraction > np.exp(-max(mean_y, 1e-4)):
                    lambda_est = max(0.1, mean_y / max(1.0 - zero_fraction, 0.05))
                    pi_est = np.clip((zero_fraction - np.exp(-lambda_est)) / (1.0 - np.exp(-lambda_est)), 0.01, 0.95)
                else:
                    pi_est = 0.05
                    lambda_est = max(0.05, mean_y)

                self.sku_params[sku_id] = {
                    "pi": float(pi_est),
                    "lambda_base": float(lambda_est),
                    "fitted": False,
                }

        return self

    def _get_intensity(self, hour: pd.Timestamp) -> float:
        slot = int((hour.dayofweek >= 5)) * 24 + hour.hour
        return self.slot_profile.get(slot, 1.0)

    def expected_rate(self, sku_id: str, hour: pd.Timestamp) -> float:
        """Expected units sold in the given hour."""
        params = self.sku_params.get(sku_id)
        if not params:
            return 0.0
        intensity = self._get_intensity(hour)
        lam = params["lambda_base"] * intensity
        return float((1.0 - params["pi"]) * lam)

    def p_zero(self, sku_id: str, hour: pd.Timestamp) -> float:
        """Probability of observing zero sales in this hour under normal trading."""
        params = self.sku_params.get(sku_id)
        if not params:
            return 1.0
        intensity = self._get_intensity(hour)
        lam = params["lambda_base"] * intensity
        p0 = params["pi"] + (1.0 - params["pi"]) * np.exp(-lam)
        return float(np.clip(p0, 1e-5, 0.9999))


def score_voids(
    velocity: pd.DataFrame,
    zip_model: ZipBaseline | None = None,
    prior: float = PRIOR_VOID,
    min_silent_hours: int = MIN_SILENT_HOURS,
    min_history_hours: int = MIN_HISTORY_HOURS,
    dispersion: float = DISPERSION,
    max_evidence_hours: int = MAX_EVIDENCE_HOURS,
) -> pd.DataFrame:
    """Score every SKU in a dense hourly velocity frame using the ZIP model.

    Returns DataFrame matching OUTPUT_COLUMNS: [sku_id, silent_hours, expected_sales, p_void].
    """
    if velocity.empty:
        return pd.DataFrame({c: pd.Series(dtype="float64" if c != "sku_id" else "object") for c in OUTPUT_COLUMNS})

    v = velocity.sort_values(["sku_id", "hour"]).reset_index(drop=True)
    if zip_model is None:
        zip_model = ZipBaseline(dispersion=dispersion).fit(v)

    # Trailing run of zero sales
    sold = v["units"] > 0
    cum_sales = sold.groupby(v["sku_id"]).cumsum()
    total_sales = cum_sales.groupby(v["sku_id"]).transform("max")
    v["trailing"] = (cum_sales == total_sales) & ~sold

    history = v[~v["trailing"]]
    n_hist = history.groupby("sku_id").size().rename("n_hist")

    tail = v[v["trailing"]]
    recent = tail[tail.groupby("sku_id").cumcount(ascending=False) < max_evidence_hours]

    out_records = []
    logit_prior = np.log(prior / (1.0 - prior))

    for sku_id in v["sku_id"].unique():
        hist_count = int(n_hist.get(sku_id, 0))
        sku_tail = tail[tail["sku_id"] == sku_id]
        silent_hrs = len(sku_tail)

        if silent_hrs < min_silent_hours or hist_count < min_history_hours:
            out_records.append({
                "sku_id": sku_id,
                "silent_hours": silent_hrs,
                "expected_sales": 0.0,
                "p_void": 0.0,
            })
            continue

        sku_recent = recent[recent["sku_id"] == sku_id]
        log_p0_sum = 0.0
        exp_sales_sum = 0.0
        for hr in sku_recent["hour"]:
            ts = pd.Timestamp(hr)
            p0 = zip_model.p_zero(sku_id, ts)
            exp_rate = zip_model.expected_rate(sku_id, ts)
            log_p0_sum += np.log(max(p0, 1e-6))
            exp_sales_sum += exp_rate

        evidence = -log_p0_sum
        p_void = _logistic(evidence / dispersion + logit_prior)

        out_records.append({
            "sku_id": sku_id,
            "silent_hours": silent_hrs,
            "expected_sales": round(float(exp_sales_sum), 2),
            "p_void": round(float(p_void), 3),
        })

    return pd.DataFrame(out_records)[OUTPUT_COLUMNS]
