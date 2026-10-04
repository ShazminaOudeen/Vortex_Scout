from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AnomalyStatus = Literal["open", "restocked", "damaged", "false_alarm"]
AuditAction = Literal["restocked", "damaged", "false_alarm"]


class Anomaly(BaseModel):
    id: str
    sku_id: str
    sku_name: str
    category: str
    aisle: str
    bay: str
    ledger_stock: int
    hours_since_last_sale: float
    p_void: float = Field(ge=0, le=1)
    status: AnomalyStatus = "open"
    detected_at: datetime
    resolved_at: datetime | None = None


class ChecklistGroup(BaseModel):
    aisle: str
    title: str
    items: list[Anomaly]


class Checklist(BaseModel):
    briefing: str
    estimated_minutes: int
    groups: list[ChecklistGroup]


class ReconcilePayload(BaseModel):
    anomaly_id: str
    action: AuditAction
    associate: str | None = None
    units: int | None = Field(default=None, ge=0)


class ReconcileResult(BaseModel):
    ok: bool
    already_resolved: bool = False  # True when the anomaly was closed before this call
    status: AnomalyStatus
    ledger_stock: int | None = None  # SKU ledger after this call
    ledger_adjustment: int = 0  # units written off the ledger by this call


class AuditStats(BaseModel):
    total: int
    restocked: int
    damaged: int
    false_alarm: int
    false_alarm_rate: float  # false_alarm / total, 0 when nothing reconciled yet


class CategoryShare(BaseModel):
    category: str
    share: float


class DashboardMetrics(BaseModel):
    revenue_recovered_lkr: float
    active_voids: int
    audit_completion_rate: float
    iri_rate: float
    category_breakdown: list[CategoryShare]
