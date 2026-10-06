"""Baseline shelf-void detector (feature B1).

Idea: a shelf void shows up as a SKU that *should* be selling but has gone quiet while the ledger
still says it is in stock. Whether a quiet spell is suspicious depends on how fast the SKU
normally sells, so we weigh the silence by how many sales we would have *expected* during it.

Formally this is a likelihood-ratio test on the SKU's trailing run of zero-sale open hours:

    H0 "normal shelf": one constant sales rate over the whole window, silence is just bad luck
    H1 "void":         the rate dropped to zero when the silence began
    evidence E = log( L(H1) / L(H0) ) = U * ln(1 + P_silent / P_history)
        U         units the SKU sold before the silence
        P_*       trading exposure (sum of the store-wide hourly profile) of the history / silence
    p_void = posterior probability of a void = logistic( E + logit(PRIOR_VOID) )

For short silences E is simply the expected number of missed sales. A fast mover silent for a few
hours scores near 1. A slow mover (most of the catalogue sells well under one line per hour) can be
silent all day without it meaning anything, so it scores near 0: only the latest trading day of
silence counts, and E can never exceed what the SKU has actually sold. That is the point: fixed rules like "no sales for 3 hours" flood supervisors with
false alarms.

The store-wide profile (lunch and evening peaks, busier weekends) is learned from all SKUs'
history. Only hours *before* the current silence are used to learn it.

This is a deliberately simple, explainable first model. The Zero-Inflated Poisson (B3) and
Isolation Forest (B4) features can be compared against it.
"""
import numpy as np
import pandas as pd

PRIOR_VOID = 0.0001      # tuned on clean synthetic data: ~0 false alarms, fast movers still caught
MIN_SILENT_HOURS = 3     # open hours of zero sales before we even consider flagging
MIN_HISTORY_HOURS = 24   # open hours of earlier history needed to trust a SKU's baseline
DISPERSION = 1.0         # >1 makes the score more cautious (real sales are clumpier than Poisson)
MAX_EVIDENCE_HOURS = 14  # only the latest trading day of silence counts as evidence (08:00-22:00)

OUTPUT_COLUMNS = ["sku_id", "silent_hours", "expected_sales", "p_void"]


def _logistic(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -50, 50)))


def score_voids(velocity: pd.DataFrame, prior: float = PRIOR_VOID, min_silent_hours: int = MIN_SILENT_HOURS,
                min_history_hours: int = MIN_HISTORY_HOURS, dispersion: float = DISPERSION,
                max_evidence_hours: int = MAX_EVIDENCE_HOURS) -> pd.DataFrame:
    """Score every SKU in a dense hourly velocity frame (as returned by get_velocity()).

    Returns one row per SKU: [sku_id, silent_hours, expected_sales, p_void].
      silent_hours    trailing run of zero-sale open hours up to the end of the data
      expected_sales  units we would normally have sold during that run (for display / "why flagged")
      p_void          0..1; 0 when the SKU is too new, not silent long enough, or never sold
    """
    if velocity.empty:
        return pd.DataFrame({c: pd.Series(dtype="float64" if c != "sku_id" else "object") for c in OUTPUT_COLUMNS})

    v = velocity.sort_values(["sku_id", "hour"]).reset_index(drop=True)
    v["slot"] = (v["day_of_week"] >= 5).astype(int) * 24 + v["hour_of_day"]

    # Trailing run of zero-sale hours = rows after each SKU's last sale (all rows if it never sold).
    sold = v["units"] > 0
    cum_sales = sold.groupby(v["sku_id"]).cumsum()
    total_sales = cum_sales.groupby(v["sku_id"]).transform("max")
    v["trailing"] = (cum_sales == total_sales) & ~sold

    history = v[~v["trailing"]]
    overall = history["units"].mean()
    if not overall > 0:  # nothing has sold anywhere
        out = pd.DataFrame({"sku_id": v["sku_id"].unique()})
        out["silent_hours"], out["expected_sales"], out["p_void"] = 0, 0.0, 0.0
        return out[OUTPUT_COLUMNS]

    # Store-wide trading rhythm: relative intensity of each (weekday/weekend, hour) slot, mean ~1.
    profile = (history.groupby("slot")["units"].mean() / overall).reindex(range(48)).fillna(1.0)
    v["profile"] = v["slot"].map(profile)
    history = v[~v["trailing"]]

    # Per-SKU: units sold before the silence (U) and the trading exposure of history vs silence.
    g = history.groupby("sku_id")
    units_hist = g["units"].sum().rename("units_hist")
    p_hist = g["profile"].sum().rename("p_hist")
    n_hist = g.size().rename("n_hist")

    # Evidence only counts the most recent `max_evidence_hours` of the silence. Otherwise a slow
    # mover would pile up "evidence" just by being quiet for days, which is normal for it.
    tail = v[v["trailing"]]
    recent = tail[tail.groupby("sku_id").cumcount(ascending=False) < max_evidence_hours]
    out = pd.DataFrame({"sku_id": v["sku_id"].unique()}).set_index("sku_id")
    out["silent_hours"] = tail.groupby("sku_id").size().reindex(out.index).fillna(0).astype(int)
    out["p_silent"] = recent.groupby("sku_id")["profile"].sum().reindex(out.index).fillna(0.0)
    out = out.join(units_hist).join(p_hist).join(n_hist)
    for c in ("units_hist", "p_hist", "n_hist"):
        out[c] = out[c].fillna(0)

    ratio = np.where(out["p_hist"] > 0, out["p_silent"] / out["p_hist"].where(out["p_hist"] > 0, 1.0), 0.0)
    out["expected_sales"] = out["units_hist"] * ratio
    evidence = out["units_hist"] * np.log1p(ratio)
    logit_prior = np.log(prior / (1 - prior))
    p = _logistic(evidence.to_numpy() / dispersion + logit_prior)
    eligible = (out["silent_hours"] >= min_silent_hours) & (out["n_hist"] >= min_history_hours)
    out["p_void"] = np.where(eligible, p, 0.0)

    out = out.reset_index()
    out["expected_sales"] = out["expected_sales"].round(2)
    out["p_void"] = out["p_void"].round(3)
    return out[OUTPUT_COLUMNS]
