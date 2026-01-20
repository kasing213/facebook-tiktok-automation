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
                            COALESCE(u.username, u.email) as merchant_name,
                            c.name as customer_name
                        FROM invoice.client_link_code lc
                        JOIN public."user" u ON lc.merchant_id = u.id
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

                # Auto-register customer in ads_alert system for promotional broadcasts
                await self.register_customer_in_ads_alert(
                    tenant_id=link_data["tenant_id"],
                    customer_id=link_data["customer_id"],
                    telegram_chat_id=telegram_chat_id,
                    customer_name=link_data["customer_name"]
                )

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
                            COALESCE(u.username, u.email) as merchant_name
                        FROM invoice.customer c
                        JOIN public."user" u ON c.merchant_id = u.id
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


    # ========== BATCH REGISTRATION METHODS ==========

    async def generate_batch_link_code(
        self,
        tenant_id: str,
        merchant_id: str,
        batch_name: Optional[str] = None,
        max_uses: Optional[int] = None,
        expires_days: Optional[int] = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a batch registration code that can be used by multiple clients.

        Args:
            tenant_id: Tenant UUID
            merchant_id: Merchant (user) UUID
            batch_name: Optional name for the batch (e.g., "Store QR", "Event Signup")
            max_uses: Maximum number of registrations (None = unlimited)
            expires_days: Days until expiration (None = never expires)

        Returns:
            Dict with code, link, batch details or None on error
        """
        try:
            code = secrets.token_urlsafe(32)

            with get_db_session() as db:
                # Build expires_at based on expires_days
                if expires_days:
                    expires_sql = f"NOW() + INTERVAL '{expires_days} days'"
                else:
                    expires_sql = "NULL"

                result = db.execute(
                    text(f"""
                        INSERT INTO invoice.client_link_code
                            (tenant_id, merchant_id, customer_id, code, is_batch, batch_name, max_uses, expires_at)
                        VALUES (:tenant_id, :merchant_id, NULL, :code, TRUE, :batch_name, :max_uses, {expires_sql})
                        RETURNING id, code, batch_name, max_uses, use_count, expires_at, created_at
                    """),
                    {
                        "tenant_id": tenant_id,
                        "merchant_id": merchant_id,
                        "code": code,
                        "batch_name": batch_name,
                        "max_uses": max_uses
                    }
                )
                db.commit()
                row = result.fetchone()
                if row:
                    bot_username = settings.TELEGRAM_BOT_USERNAME or "KS_automations_bot"
                    return {
                        "id": str(row.id),
                        "code": row.code,
                        "link": f"https://t.me/{bot_username}?start=batch_{row.code}",
                        "batch_name": row.batch_name,
                        "max_uses": row.max_uses,
                        "use_count": row.use_count,
                        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    }
                return None
        except Exception as e:
            logger.error(f"Error generating batch link code: {e}")
            return None

    async def get_next_client_sequence(
        self,
        tenant_id: str,
        merchant_id: str
    ) -> int:
        """
        Atomically get and increment the client sequence number.
        Uses database-level locking to prevent race conditions.

        Args:
            tenant_id: Tenant UUID
            merchant_id: Merchant UUID

        Returns:
            Next sequence number (1-indexed)
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        INSERT INTO invoice.tenant_client_sequence (tenant_id, merchant_id, current_sequence)
                        VALUES (:tenant_id, :merchant_id, 1)
                        ON CONFLICT (tenant_id, merchant_id)
                        DO UPDATE SET
                            current_sequence = invoice.tenant_client_sequence.current_sequence + 1,
                            updated_at = NOW()
                        RETURNING current_sequence
                    """),
                    {"tenant_id": tenant_id, "merchant_id": merchant_id}
                )
                db.commit()
                return result.scalar()
        except Exception as e:
            logger.error(f"Error getting next client sequence: {e}")
            # Fallback to timestamp-based unique number
            return int(datetime.now().timestamp() * 1000) % 100000

    async def resolve_batch_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a batch code to get associated data (WITHOUT consuming it).

        Args:
            code: The batch link code token

        Returns:
            Dict with batch code details or None if not found/expired/maxed
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT
                            lc.id as link_id,
                            lc.tenant_id,
                            lc.merchant_id,
                            lc.batch_name,
                            lc.max_uses,
                            lc.use_count,
                            lc.expires_at,
                            u.email as merchant_email,
                            COALESCE(u.username, u.email) as merchant_name
                        FROM invoice.client_link_code lc
                        JOIN public."user" u ON lc.merchant_id = u.id
                        WHERE lc.code = :code
                          AND lc.is_batch = TRUE
                          AND (lc.expires_at IS NULL OR lc.expires_at > NOW())
                    """),
                    {"code": code}
                )
                row = result.fetchone()
                if row:
                    return {
                        "link_id": str(row.link_id),
                        "tenant_id": str(row.tenant_id),
                        "merchant_id": str(row.merchant_id),
                        "batch_name": row.batch_name,
                        "max_uses": row.max_uses,
                        "use_count": row.use_count,
                        "merchant_name": row.merchant_name,
                        "merchant_email": row.merchant_email,
                        "expires_at": row.expires_at.isoformat() if row.expires_at else None
                    }
                return None
        except Exception as e:
            logger.error(f"Error resolving batch code: {e}")
            return None

    async def create_customer_with_telegram(
        self,
        tenant_id: str,
        merchant_id: str,
        name: str,
        telegram_chat_id: str,
        telegram_username: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new customer record with Telegram already linked.

        Args:
            tenant_id: Tenant UUID
            merchant_id: Merchant (user) UUID
            name: Customer name (e.g., "Client-00001")
            telegram_chat_id: Telegram chat ID
            telegram_username: Telegram username

        Returns:
            Created customer dict or None on error
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        INSERT INTO invoice.customer
                            (tenant_id, merchant_id, name, telegram_chat_id, telegram_username, telegram_linked_at)
                        VALUES (:tenant_id, :merchant_id, :name, :telegram_chat_id, :telegram_username, NOW())
                        RETURNING id, tenant_id, merchant_id, name, telegram_chat_id, telegram_username, telegram_linked_at, created_at
                    """),
                    {
                        "tenant_id": tenant_id,
                        "merchant_id": merchant_id,
                        "name": name,
                        "telegram_chat_id": telegram_chat_id,
                        "telegram_username": telegram_username
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
                        "telegram_chat_id": row.telegram_chat_id,
                        "telegram_username": row.telegram_username,
                        "telegram_linked_at": row.telegram_linked_at.isoformat() if row.telegram_linked_at else None,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    }
                return None
        except Exception as e:
            logger.error(f"Error creating customer with telegram: {e}")
            return None

    async def consume_batch_code(
        self,
        code: str,
        telegram_chat_id: str,
        telegram_username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Consume a batch code and create a new auto-named customer.

        Process:
        1. Check if telegram_chat_id already registered
        2. Validate batch code (not expired, not at max uses)
        3. Get next sequence number atomically
        4. Create customer with name "Client-XXXXX"
        5. Link Telegram to new customer
        6. Increment batch use_count

        Args:
            code: The batch link code token
            telegram_chat_id: Client's Telegram chat ID
            telegram_username: Client's Telegram username (optional)

        Returns:
            Result dict with success status and customer details
        """
        try:
            # Check if this telegram_chat_id is already registered
            existing = await self.get_customer_by_chat_id(telegram_chat_id)
            if existing:
                return {
                    "success": False,
                    "error": "already_registered",
                    "message": f"Already registered as: {existing['name']}",
                    "customer_name": existing['name']
                }

            # Resolve batch code
            batch = await self.resolve_batch_code(code)
            if not batch:
                return {
                    "success": False,
                    "error": "invalid_code",
                    "message": "Invalid or expired registration link"
                }

            # Check max uses
            if batch["max_uses"] is not None and batch["use_count"] >= batch["max_uses"]:
                return {
                    "success": False,
                    "error": "max_uses_reached",
                    "message": "This registration link has reached its maximum capacity"
                }

            # Get next sequence number and generate client name
            seq = await self.get_next_client_sequence(batch["tenant_id"], batch["merchant_id"])
            client_name = f"Client-{seq:05d}"

            # Create customer with Telegram already linked
            customer = await self.create_customer_with_telegram(
                tenant_id=batch["tenant_id"],
                merchant_id=batch["merchant_id"],
                name=client_name,
                telegram_chat_id=telegram_chat_id,
                telegram_username=telegram_username
            )

            if not customer:
                return {
                    "success": False,
                    "error": "create_failed",
                    "message": "Failed to create customer record"
                }

            # Auto-register customer in ads_alert system for promotional broadcasts
            await self.register_customer_in_ads_alert(
                tenant_id=batch["tenant_id"],
                customer_id=customer["id"],
                telegram_chat_id=telegram_chat_id,
                customer_name=customer["name"]
            )

            # Increment batch use_count
            with get_db_session() as db:
                db.execute(
                    text("""
                        UPDATE invoice.client_link_code
                        SET use_count = use_count + 1
                        WHERE id = :link_id
                    """),
                    {"link_id": batch["link_id"]}
                )
                db.commit()

            return {
                "success": True,
                "customer": customer,
                "customer_id": customer["id"],
                "customer_name": customer["name"],
                "merchant_id": batch["merchant_id"],
                "merchant_name": batch["merchant_name"],
                "tenant_id": batch["tenant_id"]
            }

        except Exception as e:
            logger.error(f"Error consuming batch code: {e}")
            return {
                "success": False,
                "error": "unexpected_error",
                "message": str(e)
            }

    async def get_merchant_batch_codes(
        self,
        tenant_id: str,
        merchant_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all batch codes for a merchant with usage statistics.

        Args:
            tenant_id: Tenant UUID
            merchant_id: Merchant UUID

        Returns:
            List of batch code dicts
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT
                            id, code, batch_name, max_uses, use_count,
                            expires_at, created_at
                        FROM invoice.client_link_code
                        WHERE tenant_id = :tenant_id
                          AND merchant_id = :merchant_id
                          AND is_batch = TRUE
                        ORDER BY created_at DESC
                    """),
                    {"tenant_id": tenant_id, "merchant_id": merchant_id}
                )
                rows = result.fetchall()
                bot_username = settings.TELEGRAM_BOT_USERNAME or "KS_automations_bot"
                return [
                    {
                        "id": str(row.id),
                        "code": row.code,
                        "link": f"https://t.me/{bot_username}?start=batch_{row.code}",
                        "batch_name": row.batch_name,
                        "max_uses": row.max_uses,
                        "use_count": row.use_count,
                        "is_active": row.expires_at is None or row.expires_at > datetime.now(),
                        "is_maxed": row.max_uses is not None and row.use_count >= row.max_uses,
                        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting merchant batch codes: {e}")
            return []

    async def delete_batch_code(
        self,
        code_id: str,
        tenant_id: str,
        merchant_id: str
    ) -> bool:
        """
        Delete a batch code (only if owned by merchant).

        Args:
            code_id: Batch code UUID
            tenant_id: Tenant UUID
            merchant_id: Merchant UUID

        Returns:
            True if deleted, False otherwise
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        DELETE FROM invoice.client_link_code
                        WHERE id = :code_id
                          AND tenant_id = :tenant_id
                          AND merchant_id = :merchant_id
                          AND is_batch = TRUE
                        RETURNING id
                    """),
                    {"code_id": code_id, "tenant_id": tenant_id, "merchant_id": merchant_id}
                )
                db.commit()
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Error deleting batch code: {e}")
            return False

    # ========== ADS ALERT INTEGRATION METHODS ==========

    async def register_customer_in_ads_alert(
        self,
        tenant_id: str,
        customer_id: str,
        telegram_chat_id: str,
        customer_name: str,
        platform: str = "telegram"
    ) -> Optional[Dict[str, Any]]:
        """
        Auto-register an invoice customer in the ads_alert.chat table.
        This allows merchants to target invoice customers with promotional broadcasts.

        Called after:
        - consume_link_code(): When a customer links their Telegram via single-client link
        - consume_batch_code(): When a customer registers via batch QR code

        Args:
            tenant_id: Tenant UUID
            customer_id: invoice.customer UUID (foreign key)
            telegram_chat_id: Telegram chat ID (used as chat_id in ads_alert)
            customer_name: Customer name for display
            platform: Platform identifier (default: "telegram")

        Returns:
            Created ads_alert.chat dict or None on error
        """
        try:
            with get_db_session() as db:
                # Check if already registered in ads_alert (by customer_id or chat_id)
                existing = db.execute(
                    text("""
                        SELECT id FROM ads_alert.chat
                        WHERE tenant_id = :tenant_id
                          AND (customer_id = :customer_id OR chat_id = :chat_id)
                    """),
                    {
                        "tenant_id": tenant_id,
                        "customer_id": customer_id,
                        "chat_id": telegram_chat_id
                    }
                ).fetchone()

                if existing:
                    logger.info(f"Customer {customer_id} already registered in ads_alert")
                    return {"id": str(existing.id), "already_exists": True}

                # Create new ads_alert.chat record linked to invoice.customer
                result = db.execute(
                    text("""
                        INSERT INTO ads_alert.chat
                            (tenant_id, customer_id, platform, chat_id, chat_name, customer_name, subscribed, is_active)
                        VALUES (:tenant_id, :customer_id, :platform, :chat_id, :chat_name, :customer_name, TRUE, TRUE)
                        RETURNING id, tenant_id, customer_id, platform, chat_id, chat_name, customer_name, subscribed, is_active, created_at
                    """),
                    {
                        "tenant_id": tenant_id,
                        "customer_id": customer_id,
                        "platform": platform,
                        "chat_id": telegram_chat_id,
                        "chat_name": customer_name,
                        "customer_name": customer_name
                    }
                )
                db.commit()
                row = result.fetchone()
                if row:
                    logger.info(f"Auto-registered customer {customer_id} in ads_alert.chat")
                    return {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "customer_id": str(row.customer_id),
                        "platform": row.platform,
                        "chat_id": row.chat_id,
                        "chat_name": row.chat_name,
                        "customer_name": row.customer_name,
                        "subscribed": row.subscribed,
                        "is_active": row.is_active,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    }
                return None
        except Exception as e:
            logger.error(f"Error registering customer in ads_alert: {e}")
            return None

    async def update_ads_alert_subscription(
        self,
        telegram_chat_id: str,
        subscribed: bool
    ) -> bool:
        """
        Update ads_alert subscription status for a customer by their Telegram chat ID.

        Used for /subscribe_ads and /unsubscribe_ads bot commands.

        Args:
            telegram_chat_id: Telegram chat ID
            subscribed: True to subscribe, False to unsubscribe

        Returns:
            True if updated, False if not found or error
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        UPDATE ads_alert.chat
                        SET subscribed = :subscribed,
                            updated_at = NOW()
                        WHERE chat_id = :chat_id
                        RETURNING id
                    """),
                    {
                        "chat_id": telegram_chat_id,
                        "subscribed": subscribed
                    }
                )
                db.commit()
                row = result.fetchone()
                if row:
                    logger.info(f"Updated ads_alert subscription for {telegram_chat_id}: subscribed={subscribed}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating ads_alert subscription: {e}")
            return False

    async def get_ads_alert_subscription_status(
        self,
        telegram_chat_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get ads_alert subscription status for a customer.

        Args:
            telegram_chat_id: Telegram chat ID

        Returns:
            Dict with subscription info or None if not found
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT id, subscribed, customer_name, is_active
                        FROM ads_alert.chat
                        WHERE chat_id = :chat_id
                    """),
                    {"chat_id": telegram_chat_id}
                )
                row = result.fetchone()
                if row:
                    return {
                        "id": str(row.id),
                        "subscribed": row.subscribed,
                        "customer_name": row.customer_name,
                        "is_active": row.is_active
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting ads_alert subscription status: {e}")
            return None


# Global service instance
client_linking_service = ClientLinkingService()
