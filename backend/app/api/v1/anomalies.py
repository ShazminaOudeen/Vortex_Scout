from fastapi import APIRouter

from app.core import store
from app.models.anomaly import Anomaly, CategoryShare, DashboardMetrics
from app.services import detection

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[Anomaly])
def list_anomalies():
    return store.list_anomalies()


@router.get("/metrics", response_model=DashboardMetrics)
def metrics():
    # TODO(Task 4): compute from real audit history.
    open_n = len(store.list_anomalies(status="open"))
    return DashboardMetrics(
        revenue_recovered_lkr=482_500,
        active_voids=open_n,
        audit_completion_rate=0.94,
        iri_rate=0.048,
        category_breakdown=[
            CategoryShare(category="Chilled Dairy", share=38),
            CategoryShare(category="Biscuits & Confectionery", share=26),
            CategoryShare(category="Dry Staples", share=18),
            CategoryShare(category="Other", share=18),
        ],
    )


@router.post("/run")
def run_detection():
    """Run shelf-void detection on the latest sales data.

    feature store -> baseline scorer (app/ml/baseline.py) -> open / refresh / clear anomalies.
    Alert rule: p_void >= settings.void_threshold AND ledger stock > 0. Returns what was flagged and
    what changed (`created` / `updated` / `cleared`) so the /simulate log can show it.

    TODO(Task 2): B3/B4 swap in the Zero-Inflated Poisson model and Isolation Forest behind the same scorer.
    """
    return detection.run_detection()
