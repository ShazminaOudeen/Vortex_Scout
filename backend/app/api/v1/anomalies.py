from fastapi import APIRouter, HTTPException

from app.core import store
from app.models.anomaly import Anomaly, DashboardMetrics, VelocityResponse
from app.services import analytics, detection

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[Anomaly])
def list_anomalies():
    return store.list_anomalies()


@router.get("/metrics", response_model=DashboardMetrics)
def metrics():
    """Real dynamic KPIs computed from current anomalies, catalog, and audit log (Feature E1)."""
    return analytics.compute_dashboard_metrics()


@router.get("/{anomaly_id}/velocity", response_model=VelocityResponse)
def anomaly_velocity(anomaly_id: str):
    """Expected vs actual hourly sales velocity for the SKU of a flagged anomaly (Feature E2)."""
    anom = store.get_anomaly(anomaly_id)
    if anom is None:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return analytics.compute_sku_velocity(anom.sku_id)



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
