# api-gateway/src/api/audit_sales.py
"""Audit Sales API routes."""

from datetime import datetime
from fastapi import APIRouter, HTTPException

from src.services.sales_service import sales_service

router = APIRouter()


@router.get("/health")
async def health():
    """Audit sales service health check."""
    stats = await sales_service.get_stats()
    return stats


@router.get("/reports/daily")
async def daily_report(date: str = None):
    """Get daily sales report."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    summary = await sales_service.get_daily_summary(date)
    return {"date": date, "summary": summary}


@router.get("/sales")
async def list_sales(limit: int = 50):
    """List sales records."""
    sales = await sales_service.get_sales(limit)
    return {"sales": sales, "count": len(sales)}


@router.get("/stats")
async def get_stats():
    """Get sales statistics."""
    return await sales_service.get_stats()
