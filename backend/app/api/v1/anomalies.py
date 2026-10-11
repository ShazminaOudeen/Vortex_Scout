from fastapi import APIRouter, HTTPException

from app.agent.explainer import explain_anomaly_details
from app.core import store
from app.models.anomaly import (
    Anomaly,
    CategoryShare,
    DashboardMetrics,
    ExplanationResponse,
    VelocityResponse,
)
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


@router.get("/{anomaly_id}/explain", response_model=ExplanationResponse)
def get_anomaly_explanation(anomaly_id: str, use_gemini: bool = True):
    """Plain-English explanation of why this anomaly was flagged (Feature C3)."""
    a = store.get_anomaly(anomaly_id)
    if a is None:
        raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found")
    rate = a.expected_sales / max(1.0, a.hours_since_last_sale) if a.expected_sales else 1.0
    return explain_anomaly_details(
        anomaly_id=a.id,
        sku_id=a.sku_id,
        sku_name=a.sku_name,
        rate=rate,
        hours=a.hours_since_last_sale,
        ledger=a.ledger_stock,
        p_void=a.p_void,
        void_type=a.void_type,
        category=a.category,
        revenue_at_risk=a.revenue_at_risk,
        expected_sales=a.expected_sales,
        use_llm=use_gemini,
    )


@router.post("/run")
def run_detection():
    """Run shelf-void detection on the latest sales data.

    Feature store -> detector -> open / refresh / clear anomalies.
    Threshold is calibrated adaptively against historical false alarm rate.
    """
    return detection.run_detection()
