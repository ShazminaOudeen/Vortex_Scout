from typing import Literal

from pydantic import BaseModel

from app.models.anomaly import Anomaly, AnomalyStatus, AuditFeedItem


class Sku(BaseModel):
    id: str
    barcode: str
    name: str
    category: str
    aisle: str
    bay: str
    ledger_stock: int
    unit_cost: float
    unit_price: float = 0


class SkuWithStatus(Sku):
    p_void: float = 0.0
    anomaly_status: AnomalyStatus | None = None
    anomaly_id: str | None = None
    has_open_anomaly: bool = False
    reconciled_today: bool = False
    risk_level: Literal["critical", "high", "normal"] = "normal"


class SkuDetail(BaseModel):
    sku: SkuWithStatus
    open_anomaly: Anomaly | None = None
    audit_history: list[AuditFeedItem] = []

