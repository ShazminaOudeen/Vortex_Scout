import json
from collections import Counter
from datetime import datetime, timedelta

import pandas as pd
import pytest

from app.generator.catalog import load_catalog, load_skus
from app.generator.generate_mock_pos import SCENARIOS, generate, generate_hours

END = datetime(2026, 9, 28, 22, 0)  # 14 days: 15 Sep - 28 Sep, includes payday 25-27
FREEZE_END = datetime(2026, 10, 3, 22, 0)


# ---- catalog -----------------------------------------------------------
def test_catalog_has_200_unique_skus():
    cat = load_catalog()
    assert len(cat) == 200
    for field in ("id", "barcode", "name"):
        assert len({s[field] for s in cat}) == 200, field


def test_starter_skus_are_unchanged():
    by_id = {s["id"]: s for s in load_catalog()}
    assert by_id["s1"]["name"] == "Munchee Super Cream Cracker 490g"
    assert (by_id["s1"]["aisle"], by_id["s1"]["bay"], by_id["s1"]["ledger_stock"]) == ("03", "3B", 70)
    assert by_id["s2"]["name"] == "Highland Fresh Milk 1L"
    assert by_id["s3"]["name"] == "Anchor Full Cream Milk Powder 400g"
    assert [f"s{i}" for i in range(1, 8)] == [s["id"] for s in load_catalog()[:7]]


def test_every_sku_is_fully_specified():
    for s in load_catalog():
        assert s["aisle"] and s["bay"] and s["category"] and s["name"]
        assert s["base_rate"] > 0 and s["unit_price"] > s["unit_cost"] > 0 and s["ledger_stock"] > 30
        assert s["bay"].startswith(str(int(s["aisle"])))  # bay 3B lives in aisle 03


def test_catalog_validates_as_sku_models():
    assert len(load_skus()) == 200


def test_categories_and_brands():
    cat = load_catalog()
    counts = Counter(s["category"] for s in cat)
    assert 8 <= len(counts) <= 10
    assert {c for c, _ in counts.most_common(2)} == {"Chilled Dairy", "Biscuits & Confectionery"}
    brands = {s["name"].split()[0] for s in cat}
    assert {"Keells", "Cargills", "Munchee", "Anchor", "Highland", "Maliban"} <= brands


# ---- volume and shape --------------------------------------------------
@pytest.fixture(scope="module")
def two_weeks():
    return generate(days=14, end=END)


def test_every_day_has_1200_to_2000_lines(two_weeks):
    per_day = two_weeks.groupby(two_weeks.timestamp.dt.date).size()
    assert len(per_day) == 14
    assert per_day.min() >= 1200 and per_day.max() <= 2000, per_day.to_dict()


def test_one_day_of_data_is_in_range():
    assert 1200 <= len(generate(days=1, end=datetime(2026, 9, 29, 22, 0))) <= 2000


def test_rows_have_the_ingest_columns(two_weeks):
    assert list(two_weeks.columns) == ["timestamp", "sku_id", "store_id", "quantity", "unit_price"]
    assert two_weeks.quantity.between(1, 2).all() and (two_weeks.unit_price > 0).all()
    assert two_weeks.timestamp.is_monotonic_increasing


def test_store_is_closed_overnight(two_weeks):
    assert two_weeks.timestamp.dt.hour.between(8, 21).all()


def test_peak_hours_sell_about_twice_as_much(two_weeks):
    by_hour = two_weeks.groupby(two_weeks.timestamp.dt.hour).size()
    peak, off = by_hour[[11, 12, 18, 19, 20]].mean(), by_hour[[8, 9, 10, 13, 14, 15, 16, 17, 21]].mean()
    assert 1.7 < peak / off < 2.3


def test_weekends_and_paydays_sell_more(two_weeks):
    per_day = two_weeks.groupby(pd.to_datetime(two_weeks.timestamp.dt.date)).size()
    weekday = per_day[per_day.index.dayofweek < 5 & ~per_day.index.day.isin([25, 26, 27])].mean()
    weekend = per_day[(per_day.index.dayofweek >= 5) & ~per_day.index.day.isin([25, 26, 27])].mean()
    payday_weekend = per_day[per_day.index.day.isin([26, 27])].mean()
    assert weekend > weekday * 1.1
    assert payday_weekend > weekend * 1.05


def test_same_seed_same_data_different_seed_different_data():
    a = generate(days=1, end=END, seed=1)
    assert a.equals(generate(days=1, end=END, seed=1))
    assert not a.equals(generate(days=1, end=END, seed=2))


# ---- phantom scenarios -------------------------------------------------
FREEZE_FROM = FREEZE_END - timedelta(hours=10)


@pytest.mark.parametrize("scenario", ["frozen", "damaged"])
def test_abrupt_phantom_has_zero_sales_for_the_whole_window(scenario):
    df = generate(days=7, phantom_sku="s1", phantom_hours=10, end=FREEZE_END, scenario=scenario)
    s1 = df[df.sku_id == "s1"]
    assert (s1.timestamp < FREEZE_FROM).sum() > 50           # sold normally before
    assert not (s1.timestamp >= FREEZE_FROM).any()           # silent during the freeze
    assert not df[(df.sku_id == "s2") & (df.timestamp >= FREEZE_FROM)].empty  # others unaffected


def test_backroom_stuck_tapers_then_stops():
    df = generate(days=7, phantom_sku="s1", phantom_hours=10, end=FREEZE_END, scenario="backroom_stuck")
    s1 = df[df.sku_id == "s1"]
    taper = s1[(s1.timestamp >= FREEZE_FROM) & (s1.timestamp < FREEZE_FROM + timedelta(hours=3))]
    assert len(taper) >= 1                                    # still trickling while the shelf drains
    assert not (s1.timestamp >= FREEZE_FROM + timedelta(hours=3)).any()


def test_scenarios_carry_the_expected_audit_action():
    assert generate(days=1, phantom_sku="s1", end=END, scenario="damaged").attrs["expected_action"] == "damaged"
    assert generate(days=1, phantom_sku="s1", end=END, scenario="frozen").attrs["expected_action"] == "restocked"
    assert generate(days=1, end=END).attrs["expected_action"] is None
    assert set(SCENARIOS) == {"frozen", "damaged", "backroom_stuck"}


def test_unknown_scenario_is_an_error():
    with pytest.raises(ValueError, match="unknown scenario"):
        generate(days=1, phantom_sku="s1", end=END, scenario="stolen")


def test_phantom_from_overrides_phantom_hours():
    df = generate(days=7, phantom_sku="s1", end=FREEZE_END, phantom_from=FREEZE_END - timedelta(hours=3))
    s1 = df[df.sku_id == "s1"]
    assert not (s1.timestamp >= FREEZE_END - timedelta(hours=3)).any()
    assert (s1.timestamp >= FREEZE_END - timedelta(hours=10)).any()


def test_generate_hours_accepts_a_noncontiguous_window_and_peak_override():
    hours = [datetime(2026, 9, 29, 9), datetime(2026, 9, 29, 15)]  # off-peak hours
    normal = generate_hours(hours, seed=3)
    peak = generate_hours(hours, seed=3, force_peak=True)
    assert set(normal.timestamp.dt.hour) <= {9, 15}
    assert len(peak) > len(normal) * 1.5
