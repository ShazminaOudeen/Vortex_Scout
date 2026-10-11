"""SKU catalogue and explorer API router (Features E5 & E6)."""
from fastapi import APIRouter

from app.models.anomaly import VelocityResponse
from app.models.sku import SkuDetail, SkuWithStatus
from app.services import analytics

router = APIRouter(prefix="/skus", tags=["skus"])


@router.get("", response_model=list[SkuWithStatus])
def list_skus():
    """Retrieve full 200-SKU catalogue with active anomaly status and risk levels (Feature E5)."""
    return analytics.list_skus_with_status()


@router.get("/{sku_id}", response_model=SkuDetail)
def get_sku_detail(sku_id: str):
    """Retrieve detailed SKU metadata, active anomaly info, and audit history (Feature E6)."""
    return analytics.get_sku_detail(sku_id)


@router.get("/{sku_id}/velocity", response_model=VelocityResponse)
def get_sku_velocity(sku_id: str):
    """Retrieve expected vs actual hourly sales velocity curve for a SKU (Features E2 & E6)."""
    return analytics.compute_sku_velocity(sku_id)
