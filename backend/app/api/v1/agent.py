from fastapi import APIRouter

from app.agent.gemini_client import build_checklist, verify_gemini_connection
from app.core import store
from app.models.anomaly import Checklist

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/checklist", response_model=Checklist)
def checklist():
    open_items = store.list_anomalies(status="open")
    return build_checklist(open_items)


@router.get("/verify")
def verify_agent():
    return verify_gemini_connection()

