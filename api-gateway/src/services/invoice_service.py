# api-gateway/src/services/invoice_service.py
"""Invoice service for PostgreSQL operations."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy import text

from src.db.postgres import get_db_session

logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for interacting with Invoice schema in PostgreSQL."""

    async def get_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get invoice service statistics for a specific tenant."""
        try:
            with get_db_session() as db:
                customers = db.execute(
                    text("SELECT COUNT(*) FROM invoice.customer WHERE tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id}
                ).scalar() or 0

                invoices = db.execute(
                    text("SELECT COUNT(*) FROM invoice.invoice WHERE tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id}
                ).scalar() or 0

                return {
                    "status": "connected",
                    "customers": customers,
                    "invoices": invoices
                }
        except Exception as e:
            logger.error(f"Error getting invoice stats: {e}")
            return {"status": "error", "message": str(e)}

    async def get_customers(self, tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of customers for a specific tenant."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT id, tenant_id, name, email, phone, address, meta, created_at, updated_at
                        FROM invoice.customer
                        WHERE tenant_id = :tenant_id
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {"tenant_id": tenant_id, "limit": limit}
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
        tenant_id: str,
        customer_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get list of invoices for a specific tenant."""
        try:
            with get_db_session() as db:
                if customer_id:
                    result = db.execute(
                        text("""
                            SELECT id, tenant_id, customer_id, invoice_number, amount, status, items, meta, created_at, updated_at
                            FROM invoice.invoice
                            WHERE tenant_id = :tenant_id AND customer_id = :customer_id
                            ORDER BY created_at DESC
                            LIMIT :limit
                        """),
                        {"tenant_id": tenant_id, "customer_id": customer_id, "limit": limit}
                    )
                else:
                    result = db.execute(
                        text("""
                            SELECT id, tenant_id, customer_id, invoice_number, amount, status, items, meta, created_at, updated_at
                            FROM invoice.invoice
                            WHERE tenant_id = :tenant_id
                            ORDER BY created_at DESC
                            LIMIT :limit
                        """),
                        {"tenant_id": tenant_id, "limit": limit}
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
        tenant_id: str,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search customers by name within a specific tenant."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT id, tenant_id, name, email, phone, address, meta, created_at, updated_at
                        FROM invoice.customer
                        WHERE tenant_id = :tenant_id AND name ILIKE :query
                        ORDER BY name
                        LIMIT :limit
                    """),
                    {"tenant_id": tenant_id, "query": f"%{query}%", "limit": limit}
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

    async def get_invoice_by_id(self, invoice_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get a single invoice by ID with mandatory tenant isolation.

        Args:
            invoice_id: The invoice UUID
            tenant_id: Tenant ID - REQUIRED for security (prevents cross-tenant data access)
        """
        try:
            with get_db_session() as db:
                # SECURITY: Always enforce tenant isolation - no unfiltered access
                query = """
                    SELECT i.id, i.tenant_id, i.customer_id, i.invoice_number,
                           i.amount, i.status, i.items, i.meta,
                           i.bank, i.expected_account, i.recipient_name, i.due_date, i.currency,
                           i.verification_status, i.verified_at, i.verified_by, i.verification_note,
                           i.early_payment_enabled, i.early_payment_discount_percentage,
                           i.early_payment_deadline, i.original_amount, i.discount_amount,
                           i.final_amount, i.pro_reward_granted, i.pro_reward_granted_at,
                           i.created_at, i.updated_at,
                           c.name as customer_name
                    FROM invoice.invoice i
                    LEFT JOIN invoice.customer c ON i.customer_id = c.id
                    WHERE i.id = :invoice_id AND i.tenant_id = :tenant_id
                """
                params = {"invoice_id": invoice_id, "tenant_id": tenant_id}
                result = db.execute(text(query), params)
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
                    "recipient_name": row.recipient_name,
                    "due_date": row.due_date.isoformat() if row.due_date else None,
                    "currency": row.currency or "KHR",
                    "verification_status": row.verification_status or "pending",
                    "verified_at": row.verified_at.isoformat() if row.verified_at else None,
                    "verified_by": row.verified_by,
                    "verification_note": row.verification_note,
                    "early_payment_enabled": row.early_payment_enabled or False,
                    "early_payment_discount_percentage": float(row.early_payment_discount_percentage) if row.early_payment_discount_percentage else 10.0,
                    "early_payment_deadline": row.early_payment_deadline.isoformat() if row.early_payment_deadline else None,
                    "original_amount": float(row.original_amount) if row.original_amount else float(row.amount),
                    "discount_amount": float(row.discount_amount) if row.discount_amount else 0.0,
                    "final_amount": float(row.final_amount) if row.final_amount else float(row.amount),
                    "pro_reward_granted": row.pro_reward_granted or False,
                    "pro_reward_granted_at": row.pro_reward_granted_at.isoformat() if row.pro_reward_granted_at else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
        except Exception as e:
            logger.error(f"Error getting invoice by ID: {e}")
            return None

    async def get_invoice_by_number(self, invoice_number: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get a single invoice by invoice number with mandatory tenant isolation.

        Args:
            invoice_number: The invoice number to look up
            tenant_id: Tenant ID - REQUIRED for security (prevents cross-tenant data access)
        """
        try:
            with get_db_session() as db:
                # SECURITY: Always enforce tenant isolation - no unfiltered access
                query = """
                    SELECT i.id, i.tenant_id, i.customer_id, i.invoice_number,
                           i.amount, i.status, i.items, i.meta,
                           i.bank, i.expected_account, i.recipient_name, i.due_date, i.currency,
                           i.verification_status, i.verified_at, i.verified_by, i.verification_note,
                           i.created_at, i.updated_at,
                           c.name as customer_name
                    FROM invoice.invoice i
                    LEFT JOIN invoice.customer c ON i.customer_id = c.id
                    WHERE i.invoice_number = :invoice_number AND i.tenant_id = :tenant_id
                """
                params = {"invoice_number": invoice_number, "tenant_id": tenant_id}

                result = db.execute(text(query), params)
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
                    "recipient_name": row.recipient_name,
                    "due_date": row.due_date.isoformat() if row.due_date else None,
                    "currency": row.currency or "KHR",
                    "verification_status": row.verification_status or "pending",
                    "verified_at": row.verified_at.isoformat() if row.verified_at else None,
                    "verified_by": row.verified_by,
                    "verification_note": row.verification_note,
                    "early_payment_enabled": row.early_payment_enabled or False,
                    "early_payment_discount_percentage": float(row.early_payment_discount_percentage) if row.early_payment_discount_percentage else 10.0,
                    "early_payment_deadline": row.early_payment_deadline.isoformat() if row.early_payment_deadline else None,
                    "original_amount": float(row.original_amount) if row.original_amount else float(row.amount),
                    "discount_amount": float(row.discount_amount) if row.discount_amount else 0.0,
                    "final_amount": float(row.final_amount) if row.final_amount else float(row.amount),
                    "pro_reward_granted": row.pro_reward_granted or False,
                    "pro_reward_granted_at": row.pro_reward_granted_at.isoformat() if row.pro_reward_granted_at else None,
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
        tenant_id: str,
        verified_by: str = "telegram-ocr-bot",
        verification_note: Optional[str] = None
    ) -> bool:
        """Update invoice verification status with mandatory tenant isolation."""
        try:
            with get_db_session() as db:
                verified_at = datetime.utcnow() if verification_status == "verified" else None

                # SECURITY: Always include tenant_id in WHERE clause to prevent cross-tenant updates
                result = db.execute(
                    text("""
                        UPDATE invoice.invoice
                        SET verification_status = :verification_status,
                            verified_at = :verified_at,
                            verified_by = :verified_by,
                            verification_note = :verification_note,
                            status = CASE WHEN :verification_status = 'verified' THEN 'paid' ELSE status END,
                            updated_at = NOW()
                        WHERE id = :invoice_id AND tenant_id = :tenant_id
                    """),
                    {
                        "invoice_id": invoice_id,
                        "tenant_id": tenant_id,
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

    async def calculate_early_payment_discount(
        self,
        original_amount: float,
        discount_percentage: float = 10.0
    ) -> Dict[str, float]:
        """Calculate early payment discount amounts."""
        try:
            original = Decimal(str(original_amount))
            discount_pct = Decimal(str(discount_percentage)) / 100
            discount_amount = original * discount_pct
            final_amount = original - discount_amount

            return {
                "original_amount": float(original),
                "discount_percentage": float(discount_percentage),
                "discount_amount": float(discount_amount),
                "final_amount": float(final_amount)
            }
        except Exception as e:
            logger.error(f"Error calculating discount: {e}")
            return {
                "original_amount": original_amount,
                "discount_percentage": 0.0,
                "discount_amount": 0.0,
                "final_amount": original_amount
            }

    async def check_early_payment_eligibility(
        self,
        invoice_id: str,
        payment_date: Optional[date] = None,
        tenant_id: str = None
    ) -> Dict[str, Any]:
        """Check if payment qualifies for early payment discount."""
        try:
            if not payment_date:
                payment_date = date.today()

            if not tenant_id:
                return {"eligible": False, "reason": "Tenant ID required for security"}

            # SECURITY: Always require tenant_id to prevent cross-tenant access
            invoice = await self.get_invoice_by_id(invoice_id, tenant_id)
            if not invoice:
                return {"eligible": False, "reason": "Invoice not found"}

            if not invoice.get("early_payment_enabled"):
                return {"eligible": False, "reason": "Early payment discount not enabled"}

            deadline = invoice.get("early_payment_deadline")
            if not deadline:
                return {"eligible": False, "reason": "No early payment deadline set"}

            # Parse deadline string to date if needed
            if isinstance(deadline, str):
                deadline = date.fromisoformat(deadline)

            if payment_date <= deadline:
                return {
                    "eligible": True,
                    "discount_percentage": invoice.get("early_payment_discount_percentage", 10.0),
                    "deadline": deadline.isoformat(),
                    "days_early": (deadline - payment_date).days
                }
            else:
                return {
                    "eligible": False,
                    "reason": f"Payment date {payment_date} is after deadline {deadline}",
                    "deadline": deadline.isoformat(),
                    "days_late": (payment_date - deadline).days
                }
        except Exception as e:
            logger.error(f"Error checking early payment eligibility: {e}")
            return {"eligible": False, "reason": f"Error: {str(e)}"}

    async def apply_early_payment_benefits(
        self,
        invoice_id: str,
        payment_date: Optional[date] = None,
        tenant_id: str = None
    ) -> Dict[str, Any]:
        """Apply early payment discount to invoice."""
        try:
            if not tenant_id:
                return {"success": False, "message": "Tenant ID required for security"}

            # SECURITY: Always pass tenant_id to prevent cross-tenant access
            eligibility = await self.check_early_payment_eligibility(invoice_id, payment_date, tenant_id)
            if not eligibility["eligible"]:
                return {"success": False, "message": eligibility["reason"]}

            # SECURITY: Always require tenant_id to prevent cross-tenant access
            invoice = await self.get_invoice_by_id(invoice_id, tenant_id)
            if not invoice:
                return {"success": False, "message": "Invoice not found"}

            # Calculate discount
            discount_info = await self.calculate_early_payment_discount(
                invoice["original_amount"],
                eligibility["discount_percentage"]
            )

            # Update invoice with discount (SECURITY: Include tenant_id for isolation)
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        UPDATE invoice.invoice
                        SET discount_amount = :discount_amount,
                            final_amount = :final_amount,
                            amount = :final_amount,
                            status = 'paid',
                            updated_at = NOW()
                        WHERE id = :invoice_id AND tenant_id = :tenant_id
                    """),
                    {
                        "invoice_id": invoice_id,
                        "tenant_id": tenant_id,
                        "discount_amount": discount_info["discount_amount"],
                        "final_amount": discount_info["final_amount"]
                    }
                )
                db.commit()

            return {
                "success": True,
                "message": "Early payment benefits applied",
                "discount_applied": discount_info["discount_amount"],
                "final_amount": discount_info["final_amount"],
                "savings_percentage": discount_info["discount_percentage"]
            }
        except Exception as e:
            logger.error(f"Error applying early payment benefits: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}


# Global service instance
invoice_service = InvoiceService()
