from typing import Literal

from fastapi import APIRouter

from app.core import store

router = APIRouter(prefix="/simulate", tags=["simulate"])


@router.post("/{scenario}")
def simulate(scenario: Literal["phantom", "normal", "reset"]):
    """Judge-demo hooks used by the /simulate page.

    TODO(Task 4): 'phantom' should use app.generator to push a frozen SKU
    through /pos/stream; 'normal' should push healthy peak-hour traffic.
    """
    if scenario == "reset":
        store.reset()
    return {"ok": True, "scenario": scenario}
