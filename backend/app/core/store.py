"""In-memory demo store so the whole pipeline works before Supabase is wired.

TODO(Task 1): replace calls to this module with Supabase queries
(see supabase/schema.sql). Keep the function signatures so the API layer
doesn't change.
"""
from datetime import datetime, timezone

from app.models.anomaly import Anomaly

_now = lambda: datetime.now(timezone.utc)  # noqa: E731


def _seed() -> dict[str, Anomaly]:
    rows = [
        Anomaly(id="a1", sku_id="s1", sku_name="Munchee Super Cream Cracker 490g", category="Biscuits & Confectionery",
                aisle="03", bay="3B", ledger_stock=70, hours_since_last_sale=14, p_void=0.93, detected_at=_now()),
        Anomaly(id="a2", sku_id="s2", sku_name="Highland Fresh Milk 1L", category="Chilled Dairy",
                aisle="05", bay="5A", ledger_stock=32, hours_since_last_sale=9, p_void=0.88, detected_at=_now()),
        Anomaly(id="a3", sku_id="s3", sku_name="Anchor Full Cream Milk Powder 400g", category="Chilled Dairy",
                aisle="05", bay="5C", ledger_stock=41, hours_since_last_sale=11, p_void=0.81, detected_at=_now()),
    ]
    return {r.id: r for r in rows}


ANOMALIES: dict[str, Anomaly] = _seed()
TRANSACTIONS: list[dict] = []
AUDIT_LOG: list[dict] = []


def reset() -> None:
    ANOMALIES.clear()
    ANOMALIES.update(_seed())
    TRANSACTIONS.clear()
    AUDIT_LOG.clear()
