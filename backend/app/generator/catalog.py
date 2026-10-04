"""Reference data: the demo store and the SKU catalog (mock_skus.json)."""
import json
from pathlib import Path

from app.models.sku import Sku

SKUS_PATH = Path(__file__).with_name("mock_skus.json")

DEMO_STORES = [{"id": "store_01", "name": "Scout Demo Store (Colombo)"}]


def load_catalog() -> list[dict]:
    """Raw catalog rows, including generator-only fields (base_rate)."""
    return json.loads(SKUS_PATH.read_text())


def load_skus() -> list[Sku]:
    return [Sku.model_validate(r) for r in load_catalog()]
