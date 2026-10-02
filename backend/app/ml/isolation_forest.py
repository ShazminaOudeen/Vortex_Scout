"""Anomaly scorer: combine ZIP residuals + consecutive-zero-hour features
with scikit-learn's IsolationForest to produce P(void) in [0, 1].

TODO(Task 2): implement. Contract used by the API layer:
    score_voids(velocity_df, zip_model) -> DataFrame[sku_id, p_void, hours_since_last_sale]
Alert rule lives in the API: p_void >= settings.void_threshold AND ledger_stock > 0.
"""
import pandas as pd

from app.ml.zip_model import ZipBaseline


def score_voids(velocity: pd.DataFrame, zip_model: ZipBaseline) -> pd.DataFrame:
    raise NotImplementedError
