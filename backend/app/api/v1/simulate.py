from typing import Literal

from fastapi import APIRouter

from app.core import store
from app.generator import demo
from app.generator.generate_mock_pos import SCENARIOS

router = APIRouter(prefix="/simulate", tags=["simulate"])


@router.post("/{scenario}")
def simulate(scenario: Literal["phantom", "normal", "reset"],
             variant: Literal["frozen", "damaged", "backroom_stuck"] = "frozen"):
    """Judge-demo hooks used by the /simulate page.

    phantom  Munchee s1 stops selling for 8 trading hours while the ledger still says 40
             (`?variant=damaged|backroom_stuck` picks another phantom type). The traffic goes
             through the real ingest path, so hourly_velocity updates exactly like production.
    normal   3 trading hours of healthy peak traffic for every SKU.
    reset    Wipes transactions, velocity, anomalies and the audit log; restores ledger stock.
             With Supabase configured this deletes rows in the live demo tables.
    """
    assert variant in SCENARIOS
    if scenario == "reset":
        store.reset()
        return {"ok": True, "scenario": scenario}
    detail = demo.inject_phantom(variant) if scenario == "phantom" else demo.inject_normal()
    return {"ok": True, "scenario": scenario, **detail}
