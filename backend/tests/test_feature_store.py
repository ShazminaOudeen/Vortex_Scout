from datetime import datetime

import pandas as pd
import pytest

from app.core import store
from app.generator.generate_mock_pos import generate
from app.ml.feature_pipeline import OPEN_HOUR, CLOSE_HOUR, VELOCITY_COLUMNS, get_velocity, hours_since_last_sale
from app.services.ingest import ingest

END = datetime(2026, 10, 3, 22, 0)  # last open hour is 21:00


@pytest.fixture
def loaded(backend):
    """2 days of traffic; s1 goes silent for the last 8 trading hours."""
    df = generate(days=2, phantom_sku="s1", phantom_hours=8, end=END)
    assert ingest(df.to_dict("records")).rejected == 0
    return df


def test_empty_store_returns_empty_frame_with_the_contract_columns(backend):
    v = get_velocity()
    assert v.empty and list(v.columns) == VELOCITY_COLUMNS
    assert hours_since_last_sale().empty


def test_contract_columns_and_dtypes(loaded):
    v = get_velocity()
    assert list(v.columns) == VELOCITY_COLUMNS
    assert pd.api.types.is_integer_dtype(v["units"]) and (v["units"] >= 0).all()
    row = v[(v.sku_id == "s2") & (v.hour == pd.Timestamp("2026-10-03 11:00"))].iloc[0]
    assert (row.hour_of_day, row.day_of_week, row.is_peak) == (11, 5, 1)  # Saturday, peak hour


def test_frame_is_dense_over_open_hours_for_every_sku(loaded):
    v = get_velocity()
    n_skus = len(store.list_skus())
    open_hours = CLOSE_HOUR - OPEN_HOUR
    assert v.sku_id.nunique() == n_skus == 200
    assert len(v) == n_skus * open_hours * 2          # 2 days, no gaps
    assert v.hour_of_day.between(OPEN_HOUR, CLOSE_HOUR - 1).all()
    assert not v.duplicated(["sku_id", "hour"]).any()


def test_zero_sale_hours_are_explicit_including_the_trailing_phantom_gap(loaded):
    v = get_velocity()
    assert (v.units == 0).any()
    s1 = v[v.sku_id == "s1"].sort_values("hour")
    assert (s1.units.tail(8) == 0).all()               # the frozen window is present as zeros
    assert (s1.units.iloc[:-8] > 0).sum() > 15         # and it sold normally before
    assert s1.hour.max() == pd.Timestamp("2026-10-03 21:00")
    assert v[v.sku_id == "s2"].units.tail(8).sum() > 0  # control SKU kept selling


def test_open_only_false_includes_closed_hours(loaded):
    v = get_velocity(open_only=False)
    assert v.hour_of_day.nunique() == 24
    closed = v[~v.hour_of_day.between(OPEN_HOUR, CLOSE_HOUR - 1)]
    assert (closed.units == 0).all()


def test_sku_and_time_filters(loaded):
    v = get_velocity(sku_id="s1", since=datetime(2026, 10, 3, 0, 0))
    assert set(v.sku_id) == {"s1"} and v.hour.min() == pd.Timestamp("2026-10-03 08:00")
    assert v.hour.max() == pd.Timestamp("2026-10-03 21:00")
    w = get_velocity(until=datetime(2026, 10, 3, 0, 0))  # exclusive upper bound
    assert w.hour.max() == pd.Timestamp("2026-10-02 21:00")


def test_hours_since_last_sale(loaded):
    h = hours_since_last_sale().set_index("sku_id")
    assert list(h.columns) == ["last_sale_hour", "hours_since_last_sale"]
    assert h.loc["s1", "hours_since_last_sale"] >= 8
    assert h.loc["s2", "hours_since_last_sale"] <= 2
    assert h.loc["s1", "last_sale_hour"] < pd.Timestamp("2026-10-03 14:00")
    assert len(h) == 200 and (h.hours_since_last_sale >= 0).all()


def test_sku_that_never_sold_gets_the_full_span(backend):
    ingest([{"timestamp": "2026-10-02T09:15:00", "sku_id": "s1", "store_id": "store_01", "quantity": 1, "unit_price": 395},
            {"timestamp": "2026-10-02T12:15:00", "sku_id": "s2", "store_id": "store_01", "quantity": 1, "unit_price": 420}])
    h = hours_since_last_sale().set_index("sku_id")
    assert pd.isna(h.loc["s9", "last_sale_hour"])
    assert h.loc["s9", "hours_since_last_sale"] == 4.0   # 09:00 -> end of the 12:00 hour (13:00)
    assert h.loc["s2", "hours_since_last_sale"] == 0.0
    assert h.loc["s1", "hours_since_last_sale"] == 3.0   # sold in the 09:00 hour, which ended at 10:00
