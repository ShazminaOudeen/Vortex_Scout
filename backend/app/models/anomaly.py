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
    units: int | None = None


class CategoryShare(BaseModel):
    category: str
    share: float


class DashboardMetrics(BaseModel):
    revenue_recovered_lkr: float
    active_voids: int
    audit_completion_rate: float
    iri_rate: float
    category_breakdown: list[CategoryShare]
