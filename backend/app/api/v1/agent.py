from fastapi import APIRouter

from app.agent.gemini_client import build_checklist
from app.core import store
from app.models.anomaly import Checklist

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/checklist", response_model=Checklist)
def checklist():
    open_items = [a for a in store.ANOMALIES.values() if a.status == "open"]
    return build_checklist(open_items)
