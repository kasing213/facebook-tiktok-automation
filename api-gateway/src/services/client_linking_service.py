# api-gateway/src/services/client_linking_service.py
"""Client linking service for merchant client registration via Telegram."""

import logging
import secrets
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy import text

from src.db.postgres import get_db_session
from src.config import settings

logger = logging.getLogger(__name__)


class ClientLinkingService:
    """Service for managing merchant client registration and Telegram linking."""

    async def create_customer(
        self,
        tenant_id: str,
        merchant_id: str,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new customer record tied to a merchant.

        Args:
            tenant_id: Tenant UUID
            merchant_id: Merchant (user) UUID
            name: Customer name
            email: Optional email
            phone: Optional phone
            address: Optional address

        Returns:
            Created customer dict or None on error
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        INSERT INTO invoice.customer (tenant_id, merchant_id, name, email, phone, address)
                        VALUES (:tenant_id, :merchant_id, :name, :email, :phone, :address)
                        RETURNING id, tenant_id, merchant_id, name, email, phone, address, created_at
                    """),
                    {
                        "tenant_id": tenant_id,
                        "merchant_id": merchant_id,
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "address": address
                    }
                )
                db.commit()
                row = result.fetchone()
                if row:
                    return {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "merchant_id": str(row.merchant_id),
                        "name": row.name,
                        "email": row.email,
                        "phone": row.phone,
                        "address": row.address,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    }
                return None
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            return None

    async def generate_link_code(
        self,
        tenant_id: str,
        merchant_id: str,
        customer_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a secure, opaque link code for client registration.

        Args:
            tenant_id: Tenant UUID
            merchant_id: Merchant (user) UUID
            customer_id: Customer UUID

        Returns:
            Dict with code and link, or None on error
        """
        try:
            # Generate cryptographically secure token (64 chars)
            code = secrets.token_urlsafe(32)

            with get_db_session() as db:
                result = db.execute(
                    text("""
                        INSERT INTO invoice.client_link_code
                            (tenant_id, merchant_id, customer_id, code)
                        VALUES (:tenant_id, :merchant_id, :customer_id, :code)
                        RETURNING id, code, expires_at
                    """),
                    {
                        "tenant_id": tenant_id,
                        "merchant_id": merchant_id,
                        "customer_id": customer_id,
                        "code": code
                    }
                )
                db.commit()
                row = result.fetchone()
                if row:
                    bot_username = settings.TELEGRAM_BOT_USERNAME or "KS_automations_bot"
                    return {
                        "id": str(row.id),
                        "code": row.code,
                        "link": f"https://t.me/{bot_username}?start=client_{row.code}",
                        "expires_at": row.expires_at.isoformat() if row.expires_at else None
                    }
                return None
        except Exception as e:
            logger.error(f"Error generating link code: {e}")
            return None

    async def resolve_link_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a link code to get associated data (WITHOUT consuming it).

        Args:
            code: The link code token

        Returns:
            Dict with tenant_id, merchant_id, customer_id, merchant_name, customer_name
            or None if not found or already used
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT
                            lc.id as link_id,
                            lc.tenant_id,
                            lc.merchant_id,
                            lc.customer_id,
                            lc.expires_at,
                            u.email as merchant_email,
                            COALESCE(u.first_name || ' ' || u.last_name, u.email) as merchant_name,
                            c.name as customer_name
                        FROM invoice.client_link_code lc
                        JOIN public.user u ON lc.merchant_id = u.id
                        JOIN invoice.customer c ON lc.customer_id = c.id
                        WHERE lc.code = :code
                          AND lc.used_at IS NULL
                          AND lc.expires_at > NOW()
                    """),
                    {"code": code}
                )
                row = result.fetchone()
                if row:
                    return {
                        "link_id": str(row.link_id),
                        "tenant_id": str(row.tenant_id),
                        "merchant_id": str(row.merchant_id),
                        "customer_id": str(row.customer_id),
                        "merchant_name": row.merchant_name,
                        "merchant_email": row.merchant_email,
                        "customer_name": row.customer_name,
                        "expires_at": row.expires_at.isoformat() if row.expires_at else None
                    }
                return None
        except Exception as e:
            logger.error(f"Error resolving link code: {e}")
            return None

    async def consume_link_code(
        self,
        code: str,
        telegram_chat_id: str,
        telegram_username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Consume a link code and update the customer with Telegram info.

        Args:
            code: The link code token
            telegram_chat_id: Client's Telegram chat ID
            telegram_username: Client's Telegram username (optional)

        Returns:
            Result dict with success status
        """
        try:
            # First check if this telegram_chat_id is already used
            with get_db_session() as db:
                existing = db.execute(
                    text("""
                        SELECT id, name FROM invoice.customer
                        WHERE telegram_chat_id = :telegram_chat_id
                    """),
                    {"telegram_chat_id": telegram_chat_id}
                ).fetchone()

                if existing:
                    return {
                        "success": False,
                        "error": "already_registered",
                        "message": f"This Telegram account is already registered as: {existing.name}"
                    }

            # Resolve the link code
            link_data = await self.resolve_link_code(code)
            if not link_data:
                return {
                    "success": False,
                    "error": "invalid_code",
                    "message": "Link code is invalid, expired, or already used"
                }

            # Update customer with Telegram info and mark code as used
            with get_db_session() as db:
                # Update customer
                db.execute(
                    text("""
                        UPDATE invoice.customer
                        SET telegram_chat_id = :telegram_chat_id,
                            telegram_username = :telegram_username,
                            telegram_linked_at = NOW(),
                            updated_at = NOW()
                        WHERE id = :customer_id
                    """),
                    {
                        "customer_id": link_data["customer_id"],
                        "telegram_chat_id": telegram_chat_id,
                        "telegram_username": telegram_username
                    }
                )

                # Mark link code as used
                db.execute(
                    text("""
                        UPDATE invoice.client_link_code
                        SET used_at = NOW()
                        WHERE id = :link_id
                    """),
                    {"link_id": link_data["link_id"]}
                )

                db.commit()

                return {
                    "success": True,
                    "customer_id": link_data["customer_id"],
                    "customer_name": link_data["customer_name"],
                    "merchant_id": link_data["merchant_id"],
                    "merchant_name": link_data["merchant_name"],
                    "tenant_id": link_data["tenant_id"]
                }

        except Exception as e:
            logger.error(f"Error consuming link code: {e}")
            return {
                "success": False,
                "error": "unexpected_error",
                "message": str(e)
            }

    async def get_merchant_clients(
        self,
        tenant_id: str,
        merchant_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get list of clients for a merchant (scoped by tenant + merchant).

        Args:
            tenant_id: Tenant UUID
            merchant_id: Merchant (user) UUID
            limit: Max results

        Returns:
            List of customer dicts
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT
                            id, tenant_id, merchant_id, name, email, phone, address,
                            telegram_chat_id, telegram_username, telegram_linked_at,
                            created_at, updated_at
                        FROM invoice.customer
                        WHERE tenant_id = :tenant_id
                          AND merchant_id = :merchant_id
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {
                        "tenant_id": tenant_id,
                        "merchant_id": merchant_id,
                        "limit": limit
                    }
                )
                rows = result.fetchall()
                return [
                    {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "merchant_id": str(row.merchant_id),
                        "name": row.name,
                        "email": row.email,
                        "phone": row.phone,
                        "address": row.address,
                        "telegram_chat_id": row.telegram_chat_id,
                        "telegram_username": row.telegram_username,
                        "telegram_linked": row.telegram_chat_id is not None,
                        "telegram_linked_at": row.telegram_linked_at.isoformat() if row.telegram_linked_at else None,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting merchant clients: {e}")
            return []

    async def get_customer_by_chat_id(
        self,
        telegram_chat_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get customer by Telegram chat ID.

        Args:
            telegram_chat_id: Telegram chat ID

        Returns:
            Customer dict or None if not found
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT
                            c.id, c.tenant_id, c.merchant_id, c.name, c.email, c.phone,
                            c.telegram_chat_id, c.telegram_username,
                            u.email as merchant_email,
                            COALESCE(u.first_name || ' ' || u.last_name, u.email) as merchant_name
                        FROM invoice.customer c
                        JOIN public.user u ON c.merchant_id = u.id
                        WHERE c.telegram_chat_id = :telegram_chat_id
                    """),
                    {"telegram_chat_id": telegram_chat_id}
                )
                row = result.fetchone()
                if row:
                    return {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "merchant_id": str(row.merchant_id),
                        "name": row.name,
                        "email": row.email,
                        "phone": row.phone,
                        "telegram_chat_id": row.telegram_chat_id,
                        "telegram_username": row.telegram_username,
                        "merchant_name": row.merchant_name,
                        "merchant_email": row.merchant_email
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting customer by chat ID: {e}")
            return None

    async def get_pending_invoices_for_customer(
        self,
        customer_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get pending (unpaid) invoices for a customer.

        Args:
            customer_id: Customer UUID

        Returns:
            List of pending invoices
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT
                            id, tenant_id, customer_id, invoice_number,
                            amount, currency, bank, expected_account,
                            status, verification_status, created_at
                        FROM invoice.invoice
                        WHERE customer_id = :customer_id
                          AND verification_status IN ('pending', 'rejected')
                          AND status != 'cancelled'
                        ORDER BY created_at DESC
                    """),
                    {"customer_id": customer_id}
                )
                rows = result.fetchall()
                return [
                    {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "customer_id": str(row.customer_id),
                        "invoice_number": row.invoice_number,
                        "amount": float(row.amount),
                        "currency": row.currency or "KHR",
                        "bank": row.bank,
                        "expected_account": row.expected_account,
                        "status": row.status,
                        "verification_status": row.verification_status,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting pending invoices: {e}")
            return []


# Global service instance
client_linking_service = ClientLinkingService()
