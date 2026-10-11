from fastapi import APIRouter, HTTPException

from app.core import store
from app.models.anomaly import (
    AuditFeedItem,
    AuditStats,
    ReconcilePayload,
    ReconcileResult,
    UndoPayload,
    UndoResult,
)
from app.services import analytics

router = APIRouter(prefix="/audit", tags=["audit"])



@router.post("/reconcile", response_model=ReconcileResult)
def reconcile(body: ReconcilePayload):
    """Log a staff action against an anomaly.

    Closes the anomaly, writes one audit_log row and simulates the ERP ledger adjustment:
      restocked   -> ledger unchanged (the ledger already believed the stock existed)
      damaged     -> ledger reduced by `units` (write-off; no change if units is omitted)
      false_alarm -> ledger unchanged
    Idempotent: reconciling an already-resolved anomaly (a double tap) changes nothing,
    writes no second audit row and returns `already_resolved: true`.

    TODO(Task 2): feed the false_alarm rate (GET /audit/stats) back to calibrate void_threshold.
    """
    anomaly = store.get_anomaly(body.anomaly_id)
    if anomaly is None:
        raise HTTPException(404, "Anomaly not found")

    claimed = store.resolve_anomaly(body.anomaly_id, body.action) if anomaly.status == "open" else None
    if claimed is None:  # already resolved (or lost a race to another tap)
        current = store.get_anomaly(body.anomaly_id) or anomaly
        sku = store.get_sku(current.sku_id)
        return ReconcileResult(ok=True, already_resolved=True, status=current.status,
                               ledger_stock=sku.ledger_stock if sku else None)

    adjustment = 0
    ledger = None
    if body.action == "damaged" and body.units:
        ledger = store.adjust_ledger_stock(claimed.sku_id, -body.units)
        adjustment = -body.units
    if ledger is None:
        sku = store.get_sku(claimed.sku_id)
        ledger = sku.ledger_stock if sku else None
    store.append_audit(claimed.id, body.action, body.associate, body.units)
    return ReconcileResult(ok=True, status=claimed.status, ledger_stock=ledger, ledger_adjustment=adjustment)


@router.post("/undo", response_model=UndoResult)
def undo_reconcile(body: UndoPayload):
    """Reverts the last reconciliation for an anomaly (Feature D5).

    Reopens the anomaly, adjusts the ledger back if damaged units were written off,
    and removes the reconciled audit record.
    """
    anomaly = store.get_anomaly(body.anomaly_id)
    if anomaly is None:
        raise HTTPException(404, "Anomaly not found")

    if anomaly.status == "open":
        sku = store.get_sku(anomaly.sku_id)
        return UndoResult(ok=True, reopened=False, anomaly_id=body.anomaly_id, status="open",
                          ledger_stock=sku.ledger_stock if sku else None)

    last_audit = store.remove_last_audit(body.anomaly_id)
    if last_audit and last_audit.get("action") == "damaged" and last_audit.get("units"):
        store.adjust_ledger_stock(anomaly.sku_id, int(last_audit["units"]))

    store.reopen_anomaly(body.anomaly_id)
    sku = store.get_sku(anomaly.sku_id)
    return UndoResult(
        ok=True,
        reopened=True,
        anomaly_id=body.anomaly_id,
        status="open",
        ledger_stock=sku.ledger_stock if sku else None,
    )


@router.get("/stats", response_model=AuditStats)
def stats():
    """Action counts over the whole audit log. Task 2 uses `false_alarm_rate` to tune the threshold."""
    c = store.audit_action_counts()
    total = sum(c.values())
    return AuditStats(total=total, restocked=c["restocked"], damaged=c["damaged"], false_alarm=c["false_alarm"],
                      false_alarm_rate=round(c["false_alarm"] / total, 4) if total else 0.0)


@router.get("/feed", response_model=list[AuditFeedItem])
def audit_feed(limit: int = 50, sku_id: str | None = None):
    """Recent staff reconciliation actions formatted as an activity feed (Feature E4)."""
    return analytics.get_audit_feed(limit=limit, sku_id=sku_id)

