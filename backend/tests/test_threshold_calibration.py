"""Tests for threshold calibration via audit feedback (Feature B5)."""
from app.core import store
from app.services.detection import calibrate_threshold, run_detection


def test_default_threshold_with_insufficient_audits(backend):
    """When audit history is small, default base threshold 0.75 is used."""
    thr, meta = calibrate_threshold(base_threshold=0.75, min_audits=5)
    assert thr == 0.75
    assert meta["status"] == "default"


def test_high_false_alarm_rate_raises_threshold(backend):
    """If associates log a high percentage of false alarms, raise threshold to reduce fatigue."""
    # Append 8 false alarms and 2 restocked (80% false alarm rate)
    for _ in range(8):
        store.append_audit(anomaly_id="a1", action="false_alarm")
    for _ in range(2):
        store.append_audit(anomaly_id="a2", action="restocked")

    thr, meta = calibrate_threshold(base_threshold=0.75, min_audits=5)
    assert thr > 0.75
    assert meta["false_alarm_rate"] == 0.8
    assert "reduce alert fatigue" in meta["reason"]


def test_low_false_alarm_rate_allows_sensitive_threshold(backend):
    """If audit history is high and false alarms are near zero, allow slight sensitivity increase."""
    # Append 15 restocked audits and 0 false alarms (0% false alarm rate)
    for _ in range(15):
        store.append_audit(anomaly_id="a1", action="restocked")

    thr, meta = calibrate_threshold(base_threshold=0.75, min_audits=5)
    assert thr <= 0.75
    assert meta["false_alarm_rate"] == 0.0
    assert meta["status"] == "sensitive"


def test_calibration_metadata_in_run_detection(client):
    """run_detection response includes calibration details and threshold."""
    res = client.post("/api/v1/anomalies/run").json()
    assert "threshold" in res
    assert "calibration" in res
    assert "base_threshold" in res["calibration"]
    assert "effective_threshold" in res["calibration"]


def test_get_threshold_endpoint(client):
    """GET /api/v1/anomalies/threshold returns calibration status."""
    res = client.get("/api/v1/anomalies/threshold")
    assert res.status_code == 200
    data = res.json()
    assert "effective_threshold" in data
    assert "status" in data
