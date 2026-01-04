# api-gateway/src/api/invoice.py
"""Invoice Generator API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException

from src.services.invoice_service import invoice_service

router = APIRouter()


@router.get("/health")
async def health():
    """Invoice service health check."""
    stats = await invoice_service.get_stats()
    return stats


@router.get("/customers")
async def list_customers(limit: int = 50):
    """List customers."""
    customers = await invoice_service.get_customers(limit)
    return {"customers": customers, "count": len(customers)}


@router.get("/customers/search")
async def search_customers(q: str, limit: int = 20):
    """Search customers by name."""
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    customers = await invoice_service.search_customers(q, limit)
    return {"customers": customers, "count": len(customers)}


@router.get("/invoices")
async def list_invoices(customer_id: Optional[str] = None, limit: int = 50):
    """List invoices."""
    invoices = await invoice_service.get_invoices(customer_id, limit)
    return {"invoices": invoices, "count": len(invoices)}


@router.get("/stats")
async def get_stats():
    """Get invoice statistics."""
    return await invoice_service.get_stats()
