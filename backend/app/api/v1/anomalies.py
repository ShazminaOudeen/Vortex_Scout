from fastapi import APIRouter

from app.core import store
from app.core.config import get_settings
from app.models.anomaly import Anomaly, CategoryShare, DashboardMetrics

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[Anomaly])
def list_anomalies():
    return list(store.ANOMALIES.values())


@router.get("/metrics", response_model=DashboardMetrics)
def metrics():
    # TODO(Task 4): compute from real audit history.
    open_n = sum(a.status == "open" for a in store.ANOMALIES.values())
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
    """Run feature pipeline -> ZIP baseline -> Isolation Forest -> filter.

    TODO(Task 2): call app.ml.* and persist results. Alert rule:
    p_void >= settings.void_threshold AND ledger_stock > 0.
    """
    thr = get_settings().void_threshold
    flagged = [a for a in store.ANOMALIES.values() if a.p_void >= thr and a.ledger_stock > 0]
    return {"flagged": len(flagged)}
