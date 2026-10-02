"""Zero-Inflated Poisson baseline: expected hourly sales per SKU.

TODO(Task 2): implement with statsmodels
  from statsmodels.discrete.count_model import ZeroInflatedPoisson
Fit per SKU (or per category if data is sparse) on features from
feature_pipeline.add_time_features(). Output: expected rate lambda and
P(structural zero) for each hour so we can tell a normal quiet hour from
a shelf void.
"""
import pandas as pd


class ZipBaseline:
    def fit(self, velocity: pd.DataFrame) -> "ZipBaseline":
        raise NotImplementedError

    def expected_rate(self, sku_id: str, hour: pd.Timestamp) -> float:
        raise NotImplementedError

    def p_zero(self, sku_id: str, hour: pd.Timestamp) -> float:
        """Probability a zero-sale hour is just normal for this SKU/time."""
        raise NotImplementedError
