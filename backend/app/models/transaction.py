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
