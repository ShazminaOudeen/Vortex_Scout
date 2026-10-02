from pydantic import BaseModel


class Sku(BaseModel):
    id: str
    barcode: str
    name: str
    category: str
    aisle: str
    bay: str
    ledger_stock: int
    unit_cost: float
