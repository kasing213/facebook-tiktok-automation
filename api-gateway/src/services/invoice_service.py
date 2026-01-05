# api-gateway/src/services/invoice_service.py
"""Invoice service for PostgreSQL operations."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy import text

from src.db.postgres import get_db_session

logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for interacting with Invoice schema in PostgreSQL."""

    async def get_stats(self) -> Dict[str, Any]:
        """Get invoice service statistics."""
        try:
            with get_db_session() as db:
                customers = db.execute(
                    text("SELECT COUNT(*) FROM invoice.customer")
                ).scalar() or 0

                invoices = db.execute(
                    text("SELECT COUNT(*) FROM invoice.invoice")
                ).scalar() or 0

                return {
                    "status": "connected",
                    "customers": customers,
                    "invoices": invoices
                }
        except Exception as e:
            logger.error(f"Error getting invoice stats: {e}")
            return {"status": "error", "message": str(e)}

    async def get_customers(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of customers."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT id, tenant_id, name, email, phone, address, meta, created_at, updated_at
                        FROM invoice.customer
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {"limit": limit}
                )
                rows = result.fetchall()
                return [
                    {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "name": row.name,
                        "email": row.email,
                        "phone": row.phone,
                        "address": row.address,
                        "meta": row.meta or {},
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting customers: {e}")
            return []

    async def get_invoices(
        self,
        customer_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get list of invoices."""
        try:
            with get_db_session() as db:
                if customer_id:
                    result = db.execute(
                        text("""
                            SELECT id, tenant_id, customer_id, invoice_number, amount, status, items, meta, created_at, updated_at
                            FROM invoice.invoice
                            WHERE customer_id = :customer_id
                            ORDER BY created_at DESC
                            LIMIT :limit
                        """),
                        {"customer_id": customer_id, "limit": limit}
                    )
                else:
                    result = db.execute(
                        text("""
                            SELECT id, tenant_id, customer_id, invoice_number, amount, status, items, meta, created_at, updated_at
                            FROM invoice.invoice
                            ORDER BY created_at DESC
                            LIMIT :limit
                        """),
                        {"limit": limit}
                    )

                rows = result.fetchall()
                return [
                    {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "customer_id": str(row.customer_id),
                        "invoice_number": row.invoice_number,
                        "amount": float(row.amount),
                        "status": row.status,
                        "items": row.items or [],
                        "meta": row.meta or {},
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting invoices: {e}")
            return []

    async def search_customers(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search customers by name."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT id, tenant_id, name, email, phone, address, meta, created_at, updated_at
                        FROM invoice.customer
                        WHERE name ILIKE :query
                        ORDER BY name
                        LIMIT :limit
                    """),
                    {"query": f"%{query}%", "limit": limit}
                )
                rows = result.fetchall()
                return [
                    {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "name": row.name,
                        "email": row.email,
                        "phone": row.phone,
                        "address": row.address,
                        "meta": row.meta or {},
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error searching customers: {e}")
            return []


# Global service instance
invoice_service = InvoiceService()
