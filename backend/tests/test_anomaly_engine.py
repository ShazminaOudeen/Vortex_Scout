from datetime import datetime, timedelta

import pytest

from app.generator.generate_mock_pos import generate
from app.ml.feature_pipeline import hourly_velocity

END = datetime(2026, 10, 2, 9, 0)


def test_generator_freezes_phantom_sku():
    df = generate(days=7, phantom_sku="s1", phantom_hours=10, end=END)
    freeze_from = END - timedelta(hours=10)
    s1 = df[df.sku_id == "s1"]
    assert (s1.timestamp < freeze_from).any()      # sold normally before
    assert not (s1.timestamp >= freeze_from).any()  # silent during the freeze
    assert not df[df.sku_id == "s2"].empty          # other SKUs unaffected


def test_hourly_velocity_has_explicit_zeros():
    df = generate(days=3, end=END)
    v = hourly_velocity(df)
    assert (v.units == 0).any()


@pytest.mark.skip(reason="TODO(Task 2): implement ZIP + Isolation Forest, then assert phantom SKU p_void >= 0.75")
def test_phantom_sku_is_flagged():
    ...
