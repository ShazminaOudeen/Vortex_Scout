from datetime import datetime

from pydantic import BaseModel, Field


class PosTransaction(BaseModel):
    timestamp: datetime
    sku_id: str
    store_id: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)


class PosBatch(BaseModel):
    transactions: list[PosTransaction]


class IngestError(BaseModel):
    index: int  # position of the row in the submitted batch
    message: str


class IngestResult(BaseModel):
    ingested: int
    rejected: int = 0
    errors: list[IngestError] = Field(default_factory=list)  # capped; `rejected` is the full count
