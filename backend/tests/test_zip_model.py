"""Tests for the Zero-Inflated Poisson (ZIP) model (Feature B3)."""
from datetime import datetime

import pandas as pd
import pytest

from app.generator.catalog import load_catalog
from app.generator.generate_mock_pos import generate
from app.ml.baseline import OUTPUT_COLUMNS, score_voids as baseline_score_voids
from app.ml.feature_pipeline import get_velocity
from app.ml.zip_model import ZipBaseline, score_voids as zip_score_voids
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


def test_empty_frame_returns_documented_columns():
    out = zip_score_voids(pd.DataFrame())
    assert out.empty
    assert list(out.columns) == OUTPUT_COLUMNS


def test_fit_and_basic_predictions(week):
    model = ZipBaseline().fit(week)
    fast = "s1"
    ts_peak = pd.Timestamp("2026-10-03 12:00:00")
    ts_quiet = pd.Timestamp("2026-10-03 08:00:00")

    rate_peak = model.expected_rate(fast, ts_peak)
    rate_quiet = model.expected_rate(fast, ts_quiet)
    p0_peak = model.p_zero(fast, ts_peak)
    p0_quiet = model.p_zero(fast, ts_quiet)

    assert rate_peak > rate_quiet > 0.0
    assert 0.0 <= p0_peak <= 1.0
    assert 0.0 <= p0_quiet <= 1.0
    assert p0_peak <= p0_quiet


def test_structural_zeros_for_slow_sellers(week):
    model = ZipBaseline().fit(week)
    slow = next(s["id"] for s in load_catalog() if s["base_rate"] < 0.15)
    fast = "s1"
    ts = pd.Timestamp("2026-10-03 09:00:00")

    assert model.p_zero(slow, ts) > model.p_zero(fast, ts)


def test_normal_trading_has_no_false_alarms(week):
    scores = zip_score_voids(week)
    assert len(scores) == 200
    assert (scores["p_void"] < THRESHOLD).all()


def test_fast_seller_silence_is_flagged(week):
    scores = zip_score_voids(silence(week, "s1", 8)).set_index("sku_id")
    assert scores.loc["s1", "silent_hours"] == 8
    assert scores.loc["s1", "p_void"] >= THRESHOLD
    assert scores.loc["s1", "expected_sales"] > 10
    assert (scores.drop(index="s1")["p_void"] < THRESHOLD).all()


def test_slow_seller_silence_is_not_falsely_flagged(week):
    slow = next(s["id"] for s in load_catalog() if s["base_rate"] < 0.15)
    scores = zip_score_voids(silence(week, slow, 14)).set_index("sku_id")
    assert scores.loc[slow, "p_void"] < THRESHOLD


def test_zip_and_baseline_agreement_on_phantom(week):
    silenced = silence(week, "s1", 8)
    b1_out = baseline_score_voids(silenced).set_index("sku_id")
    b3_out = zip_score_voids(silenced).set_index("sku_id")

    assert b1_out.loc["s1", "p_void"] >= THRESHOLD
    assert b3_out.loc["s1", "p_void"] >= THRESHOLD
