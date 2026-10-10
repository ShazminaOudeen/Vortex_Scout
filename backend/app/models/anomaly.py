from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AnomalyStatus = Literal["open", "restocked", "damaged", "false_alarm"]
AuditAction = Literal["restocked", "damaged", "false_alarm"]
VoidType = Literal["frozen", "damaged", "backroom_stuck", "shelf_void"]


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
    void_type: str = "frozen"
    suggested_action: AuditAction = "restocked"


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
    already_resolved: bool = False
    status: AnomalyStatus
    ledger_stock: int | None = None
    ledger_adjustment: int = 0


class AuditStats(BaseModel):
    total: int
    restocked: int
    damaged: int
    false_alarm: int
    false_alarm_rate: float


class CategoryShare(BaseModel):
    category: str
    share: float


class DashboardMetrics(BaseModel):
    revenue_recovered_lkr: float
    active_voids: int
    audit_completion_rate: float
    iri_rate: float
    category_breakdown: list[CategoryShare]
