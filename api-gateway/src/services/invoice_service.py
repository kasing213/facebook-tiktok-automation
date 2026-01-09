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

    async def get_invoice_by_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get a single invoice by ID with payment verification fields."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT i.id, i.tenant_id, i.customer_id, i.invoice_number,
                               i.amount, i.status, i.items, i.meta,
                               i.bank, i.expected_account, i.currency,
                               i.verification_status, i.verified_at, i.verified_by, i.verification_note,
                               i.created_at, i.updated_at,
                               c.name as customer_name
                        FROM invoice.invoice i
                        LEFT JOIN invoice.customer c ON i.customer_id = c.id::text
                        WHERE i.id = :invoice_id
                    """),
                    {"invoice_id": invoice_id}
                )
                row = result.fetchone()
                if not row:
                    return None
                return {
                    "id": str(row.id),
                    "tenant_id": str(row.tenant_id),
                    "customer_id": str(row.customer_id),
                    "customer_name": row.customer_name,
                    "invoice_number": row.invoice_number,
                    "amount": float(row.amount),
                    "status": row.status,
                    "items": row.items or [],
                    "meta": row.meta or {},
                    "bank": row.bank,
                    "expected_account": row.expected_account,
                    "currency": row.currency or "KHR",
                    "verification_status": row.verification_status or "pending",
                    "verified_at": row.verified_at.isoformat() if row.verified_at else None,
                    "verified_by": row.verified_by,
                    "verification_note": row.verification_note,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
        except Exception as e:
            logger.error(f"Error getting invoice by ID: {e}")
            return None

    async def get_invoice_by_number(self, invoice_number: str) -> Optional[Dict[str, Any]]:
        """Get a single invoice by invoice number."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT i.id, i.tenant_id, i.customer_id, i.invoice_number,
                               i.amount, i.status, i.items, i.meta,
                               i.bank, i.expected_account, i.currency,
                               i.verification_status, i.verified_at, i.verified_by, i.verification_note,
                               i.created_at, i.updated_at,
                               c.name as customer_name
                        FROM invoice.invoice i
                        LEFT JOIN invoice.customer c ON i.customer_id = c.id::text
                        WHERE i.invoice_number = :invoice_number
                    """),
                    {"invoice_number": invoice_number}
                )
                row = result.fetchone()
                if not row:
                    return None
                return {
                    "id": str(row.id),
                    "tenant_id": str(row.tenant_id),
                    "customer_id": str(row.customer_id),
                    "customer_name": row.customer_name,
                    "invoice_number": row.invoice_number,
                    "amount": float(row.amount),
                    "status": row.status,
                    "items": row.items or [],
                    "meta": row.meta or {},
                    "bank": row.bank,
                    "expected_account": row.expected_account,
                    "currency": row.currency or "KHR",
                    "verification_status": row.verification_status or "pending",
                    "verified_at": row.verified_at.isoformat() if row.verified_at else None,
                    "verified_by": row.verified_by,
                    "verification_note": row.verification_note,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
        except Exception as e:
            logger.error(f"Error getting invoice by number: {e}")
            return None

    async def update_invoice_verification(
        self,
        invoice_id: str,
        verification_status: str,
        verified_by: str = "telegram-ocr-bot",
        verification_note: Optional[str] = None
    ) -> bool:
        """Update invoice verification status."""
        try:
            with get_db_session() as db:
                verified_at = datetime.utcnow() if verification_status == "verified" else None

                db.execute(
                    text("""
                        UPDATE invoice.invoice
                        SET verification_status = :verification_status,
                            verified_at = :verified_at,
                            verified_by = :verified_by,
                            verification_note = :verification_note,
                            status = CASE WHEN :verification_status = 'verified' THEN 'paid' ELSE status END,
                            updated_at = NOW()
                        WHERE id = :invoice_id
                    """),
                    {
                        "invoice_id": invoice_id,
                        "verification_status": verification_status,
                        "verified_at": verified_at,
                        "verified_by": verified_by,
                        "verification_note": verification_note
                    }
                )
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating invoice verification: {e}")
            return False


# Global service instance
invoice_service = InvoiceService()
