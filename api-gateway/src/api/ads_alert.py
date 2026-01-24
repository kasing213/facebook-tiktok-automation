# api-gateway/src/api/ads_alert.py
"""Ads Alert (Promotions) API routes with tenant isolation."""

from fastapi import APIRouter, HTTPException, Query

from src.services.promo_service import promo_service

router = APIRouter()


@router.get("/health")
async def health(tenant_id: str = Query(..., description="Tenant ID for isolation")):
    """Ads alert service health check for a specific tenant."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    stats = await promo_service.get_stats(tenant_id)
    return stats


@router.get("/chats")
async def list_chats(
    tenant_id: str = Query(..., description="Tenant ID for isolation"),
    limit: int = 50
):
    """List registered chats for a specific tenant."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    chats = await promo_service.get_registered_chats(tenant_id, limit)
    return {"chats": chats, "count": len(chats)}


@router.get("/promotions")
async def list_promotions(
    tenant_id: str = Query(..., description="Tenant ID for isolation"),
    limit: int = 50
):
    """List promotions for a specific tenant."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    promotions = await promo_service.get_promotions(tenant_id, limit)
    return {"promotions": promotions, "count": len(promotions)}


@router.get("/status")
async def get_status(tenant_id: str = Query(..., description="Tenant ID for isolation")):
    """Get current promotion status for a specific tenant."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    status = await promo_service.get_current_status(tenant_id)
    return {"status": status}


@router.get("/stats")
async def get_stats(tenant_id: str = Query(..., description="Tenant ID for isolation")):
    """Get promo statistics for a specific tenant."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    return await promo_service.get_stats(tenant_id)
