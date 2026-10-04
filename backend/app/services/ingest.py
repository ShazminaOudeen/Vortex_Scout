"""POS ingestion: validate -> chunked insert -> refresh hourly_velocity for the touched hours."""
from collections.abc import Iterable

from pydantic import ValidationError

from app.core import store
from app.core.config import get_settings
from app.core.timeutil import floor_hour, to_store_time
from app.models.transaction import IngestError, IngestResult, PosTransaction

MAX_ERRORS_LISTED = 100  # `rejected` always carries the full count


def _describe(e: ValidationError) -> str:
    return "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors())


def ingest(items: Iterable[PosTransaction | dict]) -> IngestResult:
    """Ingest POS rows. Invalid rows (bad fields, unknown sku_id/store_id) are rejected one by one
    and reported; the rest are stored. Rows may be PosTransaction objects or raw dicts (CSV)."""
    known_skus = {s.id for s in store.list_skus()}
    known_stores = {s["id"] for s in store.list_stores()}

    valid: list[dict] = []
    errors: list[IngestError] = []
    rejected = 0

    def reject(index: int, message: str) -> None:
        nonlocal rejected
        rejected += 1
        if len(errors) < MAX_ERRORS_LISTED:
            errors.append(IngestError(index=index, message=message))

    for i, item in enumerate(items):
        try:
            t = item if isinstance(item, PosTransaction) else PosTransaction.model_validate(item)
        except ValidationError as e:
            reject(i, _describe(e))
            continue
        if t.sku_id not in known_skus:
            reject(i, f"unknown sku_id '{t.sku_id}'")
        elif t.store_id not in known_stores:
            reject(i, f"unknown store_id '{t.store_id}'")
        else:
            valid.append({"store_id": t.store_id, "sku_id": t.sku_id, "timestamp": to_store_time(t.timestamp),
                          "quantity": t.quantity, "unit_price": t.unit_price})

    size = max(1, get_settings().ingest_chunk_size)
    for i in range(0, len(valid), size):
        store.insert_transactions(valid[i:i + size])
    store.refresh_hourly_velocity({(r["store_id"], r["sku_id"], floor_hour(r["timestamp"])) for r in valid})
    return IngestResult(ingested=len(valid), rejected=rejected, errors=errors)
