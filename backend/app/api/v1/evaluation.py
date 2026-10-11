from __future__ import annotations

from fastapi import APIRouter, Query

from app.ml.evaluation import (
    DEFAULT_THRESHOLD,
    define_benchmark_scenarios,
    get_or_run_evaluation,
    run_benchmark_suite,
)
from app.models.evaluation import EvaluationReport

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("", response_model=EvaluationReport)
def get_evaluation(fresh: bool = Query(False, description="Whether to recompute live instead of reading cache")):
    """Get the model evaluation benchmark report comparing Naive Rule vs Baseline vs ZIP vs Scout Ensemble."""
    if fresh:
        return run_benchmark_suite(quick=False)
    return get_or_run_evaluation(quick_if_missing=False)


@router.post("/run", response_model=EvaluationReport)
def run_evaluation(
    quick: bool = Query(False, description="Run quick 3-scenario subset (<2s) or full 6-scenario suite"),
    threshold: float = Query(DEFAULT_THRESHOLD, ge=0.1, le=0.99, description="Void probability classification threshold"),
):
    """Trigger a fresh live benchmark run across the evaluation suite and update the report."""
    return run_benchmark_suite(quick=quick, threshold=threshold)


@router.get("/scenarios")
def list_benchmark_scenarios():
    """List all standardized evaluation scenarios included in the benchmark."""
    return define_benchmark_scenarios()
