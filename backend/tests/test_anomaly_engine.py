from datetime import datetime, timedelta

from app.generator.generate_mock_pos import generate
from app.ml.feature_pipeline import get_velocity, hourly_velocity
from app.ml.isolation_forest import score_voids
from app.services.ingest import ingest

END = datetime(2026, 10, 2, 9, 0)
END_TRADING = datetime(2026, 10, 2, 22, 0)  # end of trading day at store closing (22:00)


def test_generator_freezes_phantom_sku():
    df = generate(days=7, phantom_sku="s1", phantom_hours=10, end=END)
    freeze_from = END - timedelta(hours=10)
    s1 = df[df.sku_id == "s1"]
    assert (s1.timestamp < freeze_from).any()       # sold normally before
    assert not (s1.timestamp >= freeze_from).any()   # silent during the freeze
    assert not df[df.sku_id == "s2"].empty           # other SKUs unaffected


def test_hourly_velocity_has_explicit_zeros():
    df = generate(days=3, end=END)
    v = hourly_velocity(df)
    assert (v.units == 0).any()


def test_phantom_sku_is_flagged(backend):
    """B3 + B4: Isolation Forest + ZIP baseline flags the frozen phantom SKU."""
    pos_data = generate(days=7, phantom_sku="s1", phantom_hours=8, end=END_TRADING, seed=42)
    ingest(pos_data.to_dict("records"))
    velocity = get_velocity()
    scores = score_voids(velocity).set_index("sku_id")

    assert "s1" in scores.index
    assert scores.loc["s1", "p_void"] >= 0.75
    assert scores.loc["s1", "silent_hours"] >= 8
