"""Tests for Isolation Forest and blended anomaly scorer (Feature B4)."""
from datetime import datetime

import pandas as pd
import pytest

from app.generator.catalog import load_catalog
from app.generator.generate_mock_pos import generate
from app.ml.feature_pipeline import get_velocity
from app.ml.isolation_forest import extract_features, score_voids
from app.services.ingest import ingest

END = datetime(2026, 10, 3, 22, 0)
THRESHOLD = 0.75


def silence(frame: pd.DataFrame, sku_id: str, hours: int) -> pd.DataFrame:
    out = frame.copy()
    out.loc[out[out.sku_id == sku_id].sort_values("hour").tail(hours).index, "units"] = 0
    return out


@pytest.fixture
def week(backend):
    """A week of normal store trading as a dense velocity frame."""
    ingest(generate(days=7, end=END, seed=42).to_dict("records"))
    return get_velocity()


def test_empty_frame_returns_proper_columns():
    out = score_voids(pd.DataFrame())
    assert out.empty
    assert "sku_id" in out.columns and "p_void" in out.columns


def test_feature_extraction_contains_expected_columns(week):
    features = extract_features(week)
    assert len(features) == 200
    expected_cols = {"sku_id", "silent_hours", "expected_sales", "history_rate", "silence_exposure_ratio"}
    assert expected_cols.issubset(set(features.columns))


def test_normal_trading_has_no_false_alarms(week):
    scores = score_voids(week)
    assert len(scores) == 200
    assert (scores["p_void"] < THRESHOLD).all()


def test_fast_seller_silence_is_flagged_by_isolation_forest(week):
    silenced = silence(week, "s1", 8)
    scores = score_voids(silenced).set_index("sku_id")
    assert scores.loc["s1", "silent_hours"] == 8
    assert scores.loc["s1", "p_void"] >= THRESHOLD
    assert scores.loc["s1", "expected_sales"] > 10
    assert (scores.drop(index="s1")["p_void"] < THRESHOLD).all()


def test_slow_seller_is_not_flagged(week):
    slow = next(s["id"] for s in load_catalog() if s["base_rate"] < 0.15)
    silenced = silence(week, slow, 14)
    scores = score_voids(silenced).set_index("sku_id")
    assert scores.loc[slow, "p_void"] < THRESHOLD
