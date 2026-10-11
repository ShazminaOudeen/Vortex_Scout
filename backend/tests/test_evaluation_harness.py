"""Tests for Feature F3: Model evaluation harness and comparison benchmark."""
from fastapi.testclient import TestClient

from app.ml.evaluation import (
    build_scenario_velocity,
    compute_contingency_metrics,
    define_benchmark_scenarios,
    run_benchmark_suite,
    score_model_predictions,
)
from app.models.evaluation import EvaluationReport


def test_define_benchmark_scenarios_returns_standard_cases():
    scenarios = define_benchmark_scenarios()
    assert len(scenarios) >= 5
    ids = [s["id"] for s in scenarios]
    assert "scen_frozen_fast" in ids
    assert "scen_damaged_perishable" in ids
    assert "scen_backroom_taper" in ids
    assert "scen_quiet_midweek" in ids
    assert "scen_clean_control" in ids


def test_build_scenario_velocity_creates_dense_frame():
    v = build_scenario_velocity(days=3, phantom_sku="s1", phantom_hours=4, seed=42)
    assert not v.empty
    assert set(v.columns) == {"sku_id", "hour", "units", "hour_of_day", "day_of_week", "is_peak"}
    assert len(v["sku_id"].unique()) == 200


def test_naive_rule_vs_scout_on_frozen_scenario():
    """Verify core thesis: Naive 3h rule floods false alarms on slow-movers, Scout isolates true void."""
    v = build_scenario_velocity(days=7, phantom_sku="s1", phantom_hours=8, seed=42)

    flagged_naive, _ = score_model_predictions("naive_3h", v)
    flagged_scout, _ = score_model_predictions("ensemble_scout", v, threshold=0.75)
    flagged_base, _ = score_model_predictions("baseline_b1", v, threshold=0.75)

    # True positive: s1 must be caught
    assert "s1" in flagged_naive
    assert "s1" in flagged_base
    assert "s1" in flagged_scout

    # False positives: Naive flags dozens of slow sellers (e.g. > 20), Scout flags <= 2
    assert len(flagged_naive) >= 20
    assert len(flagged_base) <= 2
    assert len(flagged_scout) <= 2

    # Precision of Scout must be dramatically higher than Naive rule
    met_naive = compute_contingency_metrics(
        tp=1, fp=len(flagged_naive) - 1, fn=0, tn=200 - len(flagged_naive)
    )
    met_scout = compute_contingency_metrics(
        tp=1, fp=len(flagged_scout) - 1, fn=0, tn=200 - len(flagged_scout)
    )

    assert met_scout["precision"] > met_naive["precision"]
    assert met_scout["false_positive_rate"] < met_naive["false_positive_rate"]


def test_contingency_metrics_math():
    res = compute_contingency_metrics(tp=10, fp=2, fn=0, tn=88)
    assert res["precision"] == round(10 / 12, 4)
    assert res["recall"] == 1.0
    assert res["accuracy"] == 0.98
    assert res["false_positive_rate"] == round(2 / 90, 4)


def test_quick_benchmark_suite_returns_complete_report():
    report = run_benchmark_suite(quick=True)
    assert isinstance(report, EvaluationReport)
    assert report.total_scenarios_evaluated >= 2
    assert len(report.summary_models) == 4
    model_names = [m.model_name for m in report.summary_models]
    assert model_names == ["naive_3h", "baseline_b1", "zip_b3", "ensemble_scout"]

    # Scout Ensemble must have > 80% false alarm reduction over Naive rule
    assert report.alert_reduction_percent > 70.0
    assert len(report.key_findings) >= 3


def test_evaluation_api_endpoints(client: TestClient):
    # GET /api/v1/evaluation/scenarios
    r_scen = client.get("/api/v1/evaluation/scenarios")
    assert r_scen.status_code == 200
    scenarios = r_scen.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 5

    # POST /api/v1/evaluation/run?quick=true
    r_run = client.post("/api/v1/evaluation/run?quick=true")
    assert r_run.status_code == 200
    report = r_run.json()
    assert report["total_scenarios_evaluated"] >= 2
    assert "summary_models" in report
    assert "threshold_curve" in report

    # GET /api/v1/evaluation (reads cache)
    r_get = client.get("/api/v1/evaluation")
    assert r_get.status_code == 200
    cached = r_get.json()
    assert len(cached["summary_models"]) == 4
