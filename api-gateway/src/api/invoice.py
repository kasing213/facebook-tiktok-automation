# api-gateway/src/api/invoice.py
"""Invoice Generator API routes with tenant isolation."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from src.services.invoice_service import invoice_service

router = APIRouter()


@router.get("/health")
async def health(tenant_id: str = Query(..., description="Tenant ID for isolation")):
    """Invoice service health check for a specific tenant."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    stats = await invoice_service.get_stats(tenant_id)
    return stats


@router.get("/customers")
async def list_customers(
    tenant_id: str = Query(..., description="Tenant ID for isolation"),
    limit: int = 50
):
    """List customers for a specific tenant."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    customers = await invoice_service.get_customers(tenant_id, limit)
    return {"customers": customers, "count": len(customers)}


@router.get("/customers/search")
async def search_customers(
    tenant_id: str = Query(..., description="Tenant ID for isolation"),
    q: str = Query(..., min_length=2),
    limit: int = 20
):
    """Search customers by name within a specific tenant."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    customers = await invoice_service.search_customers(tenant_id, q, limit)
    return {"customers": customers, "count": len(customers)}


@router.get("/invoices")
async def list_invoices(
    tenant_id: str = Query(..., description="Tenant ID for isolation"),
    customer_id: Optional[str] = None,
    limit: int = 50
):
    """List invoices for a specific tenant."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    invoices = await invoice_service.get_invoices(tenant_id, customer_id, limit)
    return {"invoices": invoices, "count": len(invoices)}


@router.get("/stats")
async def get_stats(tenant_id: str = Query(..., description="Tenant ID for isolation")):
    """Get invoice statistics for a specific tenant."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    return await invoice_service.get_stats(tenant_id)
