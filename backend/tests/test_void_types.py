"""Tests for void type classification and suggested audit actions (Feature B6)."""
from datetime import datetime
import pandas as pd
import pytest

from app.core import store
from app.generator.generate_mock_pos import generate
from app.ml.feature_pipeline import hourly_velocity
from app.ml.void_classifier import classify_void

END = datetime(2026, 10, 6, 22, 0)


def test_classify_void_frozen_on_dry_category():
    """Abrupt silence in a dry goods category is classified as 'frozen' with 'restocked'."""
    df = generate(days=7, phantom_sku="s1", scenario="frozen", end=END, seed=42)
    v = hourly_velocity(df)
    void_type, action = classify_void("s1", v, category="Biscuits & Confectionery")
    assert void_type == "frozen"
    assert action == "restocked"


def test_classify_void_perishable_is_damaged():
    """Abrupt silence in a perishable category is classified as 'damaged' with 'damaged'."""
    df = generate(days=7, phantom_sku="s2", scenario="damaged", end=END, seed=42)
    v = hourly_velocity(df)
    void_type, action = classify_void("s2", v, category="Chilled Dairy")
    assert void_type == "damaged"
    assert action == "damaged"


def test_classify_void_backroom_stuck_with_tapering():
    """Tapering sales before silence are classified as 'backroom_stuck' with 'restocked'."""
    df = generate(days=7, phantom_sku="s1", scenario="backroom_stuck", end=END, seed=42)
    v = hourly_velocity(df)
    void_type, action = classify_void("s1", v, category="Biscuits & Confectionery")
    assert void_type in ("backroom_stuck", "frozen")
    assert action == "restocked"


def test_classify_void_empty_dataframe_fallback():
    """Empty dataframe safely falls back to ('frozen', 'restocked')."""
    void_type, action = classify_void("s1", pd.DataFrame())
    assert void_type == "frozen"
    assert action == "restocked"


def test_detection_run_annotates_void_types_in_alerts(client):
    """POST /anomalies/run includes void_type and suggested_action on all alerts."""
    client.post("/api/v1/simulate/phantom")
    r = client.post("/api/v1/anomalies/run").json()
    assert r["flagged"] >= 1
    s1 = next(a for a in r["alerts"] if a["sku_id"] == "s1")
    assert "void_type" in s1 and s1["void_type"] in ("frozen", "damaged", "backroom_stuck")
    assert "suggested_action" in s1 and s1["suggested_action"] in ("restocked", "damaged")


def test_anomaly_store_preserves_void_type(client):
    """Stored anomalies retain their void_type and suggested_action."""
    client.post("/api/v1/simulate/phantom")
    client.post("/api/v1/anomalies/run")
    anomalies = client.get("/api/v1/anomalies").json()
    open_a = [a for a in anomalies if a["status"] == "open"]
    assert len(open_a) >= 1
    for a in open_a:
        assert hasattr(store.get_anomaly(a["id"]), "void_type")
        assert a.get("void_type") is not None
        assert a.get("suggested_action") in ("restocked", "damaged")
