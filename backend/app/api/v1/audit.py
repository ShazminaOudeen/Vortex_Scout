from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.core import store
from app.models.anomaly import ReconcilePayload

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/reconcile")
def reconcile(body: ReconcilePayload):
    """Log a staff action against an anomaly.

    TODO(Task 1): write audit_log row + simulated ERP ledger adjustment.
    TODO(Task 2): feed 'false_alarm' rate back to calibrate void_threshold.
    """
    anomaly = store.ANOMALIES.get(body.anomaly_id)
    if anomaly is None:
        raise HTTPException(404, "Anomaly not found")
    anomaly.status = body.action
    store.AUDIT_LOG.append(
        {**body.model_dump(), "at": datetime.now(timezone.utc).isoformat()}
    )
    return {"ok": True}
