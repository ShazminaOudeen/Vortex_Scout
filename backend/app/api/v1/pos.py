from fastapi import APIRouter

from app.core import store
from app.models.transaction import PosBatch

router = APIRouter(prefix="/pos", tags=["pos"])


@router.post("/stream")
def ingest(batch: PosBatch):
    """Batch-ingest POS rows [timestamp, sku_id, store_id, quantity, unit_price].

    TODO(Task 1): insert into pos_transactions + refresh hourly_velocity (Supabase).
    """
    store.TRANSACTIONS.extend(t.model_dump(mode="json") for t in batch.transactions)
    return {"ingested": len(batch.transactions)}
