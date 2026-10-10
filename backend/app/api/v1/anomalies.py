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


@router.get("/threshold")
def get_threshold_calibration():
    """Current calibrated void threshold and feedback status based on audit history (Feature B5)."""
    return detection.get_threshold_status()


@router.post("/run")
def run_detection():
    """Run shelf-void detection on the latest sales data.

    Feature store -> detector -> open / refresh / clear anomalies.
    Threshold is calibrated adaptively against historical false alarm rate.
    """
    return detection.run_detection()
