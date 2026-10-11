from fastapi import APIRouter

from app.agent import gemini_client
from app.core import store
from app.models.anomaly import Checklist

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/checklist", response_model=Checklist)
def checklist():
    open_items = store.list_anomalies(status="open")
    return gemini_client.build_checklist(open_items)


@router.get("/verify")
def verify_agent():
    return gemini_client.verify_gemini_connection()

