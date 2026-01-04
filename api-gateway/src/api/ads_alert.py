# api-gateway/src/api/ads_alert.py
"""Ads Alert (Promotions) API routes."""

from fastapi import APIRouter

from src.services.promo_service import promo_service

router = APIRouter()


@router.get("/health")
async def health():
    """Ads alert service health check."""
    stats = await promo_service.get_stats()
    return stats


@router.get("/chats")
async def list_chats(limit: int = 50):
    """List registered chats."""
    chats = await promo_service.get_registered_chats(limit)
    return {"chats": chats, "count": len(chats)}


@router.get("/promotions")
async def list_promotions(limit: int = 50):
    """List promotions."""
    promotions = await promo_service.get_promotions(limit)
    return {"promotions": promotions, "count": len(promotions)}


@router.get("/status")
async def get_status():
    """Get current promotion status."""
    status = await promo_service.get_current_status()
    return {"status": status}


@router.get("/stats")
async def get_stats():
    """Get promo statistics."""
    return await promo_service.get_stats()
