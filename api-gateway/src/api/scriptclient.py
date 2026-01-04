# api-gateway/src/api/scriptclient.py
"""Scriptclient (Screenshot Verifier) API routes."""

from fastapi import APIRouter

from src.services.screenshot_service import screenshot_service

router = APIRouter()


@router.get("/health")
async def health():
    """Scriptclient service health check."""
    stats = await screenshot_service.get_stats()
    return stats


@router.get("/screenshots/verified")
async def list_verified(limit: int = 50):
    """List verified screenshots."""
    screenshots = await screenshot_service.get_verified_screenshots(limit)
    return {"screenshots": screenshots, "count": len(screenshots)}


@router.get("/screenshots/pending")
async def list_pending(limit: int = 50):
    """List pending screenshots."""
    screenshots = await screenshot_service.get_pending_screenshots(limit)
    return {"screenshots": screenshots, "count": len(screenshots)}


@router.get("/stats")
async def get_stats():
    """Get screenshot statistics."""
    return await screenshot_service.get_stats()
