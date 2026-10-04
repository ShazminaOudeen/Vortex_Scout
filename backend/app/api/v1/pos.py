import io

import pandas as pd
from fastapi import APIRouter, HTTPException, Request, Response

from app.core.config import get_settings
from app.models.transaction import IngestResult, PosBatch
from app.services.ingest import ingest as ingest_rows

router = APIRouter(prefix="/pos", tags=["pos"])

CSV_COLUMNS = {"timestamp", "sku_id", "quantity", "unit_price"}  # store_id is optional


def _respond(result: IngestResult, response: Response) -> IngestResult:
    if result.ingested == 0 and result.rejected > 0:  # nothing usable in the batch
        response.status_code = 422
    return result


@router.post("/stream", response_model=IngestResult)
def ingest(batch: PosBatch, response: Response):
    """Batch-ingest POS rows [timestamp, sku_id, store_id, quantity, unit_price].

    Rows are validated individually: unknown sku_id/store_id rows are rejected and listed in
    `errors` while the rest are stored (200). If *every* row is rejected the status is 422.
    hourly_velocity is refreshed for the affected hours.
    """
    return _respond(ingest_rows(batch.transactions), response)


@router.post("/stream/csv", response_model=IngestResult)
async def ingest_csv(request: Request, response: Response):
    """Same as /stream but the body is raw CSV (Content-Type: text/csv) with a header row
    timestamp,sku_id,quantity,unit_price[,store_id] -- the format generate_mock_pos.py writes."""
    body = await request.body()
    try:
        df = pd.read_csv(io.BytesIO(body), dtype=str)
    except Exception as e:  # empty body, malformed CSV
        raise HTTPException(422, f"Could not parse CSV: {e}") from e
    missing = CSV_COLUMNS - set(df.columns)
    if missing:
        raise HTTPException(422, f"CSV is missing column(s): {', '.join(sorted(missing))}")
    if "store_id" not in df.columns:
        df["store_id"] = get_settings().default_store_id
    df["store_id"] = df["store_id"].fillna(get_settings().default_store_id)
    return _respond(ingest_rows(df.to_dict("records")), response)
