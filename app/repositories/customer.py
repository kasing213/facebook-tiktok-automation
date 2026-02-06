"""Customer repository for invoice.customer table operations."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID


class CustomerRepository:
    """Repository for invoice.customer table operations with tenant isolation."""

    @staticmethod
    def create(
        db: Session,
        tenant_id: UUID,
        merchant_id: UUID,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None
    ) -> dict:
        """
        Create a new customer in invoice.customer table.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            merchant_id: Merchant (user) UUID who owns this customer
            name: Customer name (required)
            email: Customer email (optional)
            phone: Customer phone (optional)
            address: Customer address (optional)

        Returns:
            dict: Created customer data
        """
        query = text("""
            INSERT INTO invoice.customer
            (tenant_id, merchant_id, name, email, phone, address, created_at, updated_at)
            VALUES
            (:tenant_id, :merchant_id, :name, :email, :phone, :address, NOW(), NOW())
            RETURNING
                id, tenant_id, merchant_id, name, email, phone, address,
                telegram_chat_id, telegram_username, telegram_linked_at,
                created_at, updated_at
        """)

        result = db.execute(query, {
            "tenant_id": str(tenant_id),
            "merchant_id": str(merchant_id),
            "name": name,
            "email": email,
            "phone": phone,
            "address": address
        })
        row = result.fetchone()
        db.commit()

        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "merchant_id": str(row.merchant_id),
            "name": row.name,
            "email": row.email,
            "phone": row.phone,
            "address": row.address,
            "telegram_chat_id": row.telegram_chat_id,
            "telegram_username": row.telegram_username,
            "telegram_linked_at": row.telegram_linked_at.isoformat() if row.telegram_linked_at else None,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat()
        }

    @staticmethod
    def get_by_id(db: Session, customer_id: UUID, tenant_id: UUID) -> Optional[dict]:
        """
        Get customer by ID with tenant isolation.

        Args:
            db: Database session
            customer_id: Customer UUID
            tenant_id: Tenant UUID for isolation

        Returns:
            dict or None: Customer data if found and belongs to tenant
        """
        query = text("""
            SELECT
                id, tenant_id, merchant_id, name, email, phone, address,
                telegram_chat_id, telegram_username, telegram_linked_at,
                created_at, updated_at
            FROM invoice.customer
            WHERE id = :customer_id AND tenant_id = :tenant_id
        """)

        result = db.execute(query, {
            "customer_id": str(customer_id),
            "tenant_id": str(tenant_id)
        })
        row = result.fetchone()

        if not row:
            return None

        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "merchant_id": str(row.merchant_id),
            "name": row.name,
            "email": row.email,
            "phone": row.phone,
            "address": row.address,
            "telegram_chat_id": row.telegram_chat_id,
            "telegram_username": row.telegram_username,
            "telegram_linked_at": row.telegram_linked_at.isoformat() if row.telegram_linked_at else None,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat()
        }

    @staticmethod
    def list_by_tenant(
        db: Session,
        tenant_id: UUID,
        limit: int = 50,
        skip: int = 0,
        search: Optional[str] = None
    ) -> List[dict]:
        """
        List customers for a tenant with optional search and pagination.

        Args:
            db: Database session
            tenant_id: Tenant UUID for isolation
            limit: Max number of results (default: 50)
            skip: Number of results to skip (default: 0)
            search: Optional search string for name/email/phone

        Returns:
            list: List of customer dicts
        """
        if search:
            query = text("""
                SELECT
                    id, tenant_id, merchant_id, name, email, phone, address,
                    telegram_chat_id, telegram_username, telegram_linked_at,
                    created_at, updated_at
                FROM invoice.customer
                WHERE tenant_id = :tenant_id
                  AND (
                      name ILIKE :search
                      OR email ILIKE :search
                      OR phone ILIKE :search
                  )
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
            """)
            params = {
                "tenant_id": str(tenant_id),
                "search": f"%{search}%",
                "limit": limit,
                "skip": skip
            }
        else:
            query = text("""
                SELECT
                    id, tenant_id, merchant_id, name, email, phone, address,
                    telegram_chat_id, telegram_username, telegram_linked_at,
                    created_at, updated_at
                FROM invoice.customer
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
            """)
            params = {
                "tenant_id": str(tenant_id),
                "limit": limit,
                "skip": skip
            }

        result = db.execute(query, params)
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
                "telegram_linked_at": row.telegram_linked_at.isoformat() if row.telegram_linked_at else None,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat()
            }
            for row in rows
        ]

    @staticmethod
    def update(
        db: Session,
        customer_id: UUID,
        tenant_id: UUID,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None
    ) -> Optional[dict]:
        """
        Update customer with tenant isolation.

        Args:
            db: Database session
            customer_id: Customer UUID
            tenant_id: Tenant UUID for isolation
            name: New name (optional)
            email: New email (optional)
            phone: New phone (optional)
            address: New address (optional)

        Returns:
            dict or None: Updated customer data if found and belongs to tenant
        """
        updates = []
        params = {
            "customer_id": str(customer_id),
            "tenant_id": str(tenant_id)
        }

        if name is not None:
            updates.append("name = :name")
            params["name"] = name
        if email is not None:
            updates.append("email = :email")
            params["email"] = email
        if phone is not None:
            updates.append("phone = :phone")
            params["phone"] = phone
        if address is not None:
            updates.append("address = :address")
            params["address"] = address

        if not updates:
            return CustomerRepository.get_by_id(db, customer_id, tenant_id)

        updates.append("updated_at = NOW()")
        query = text(f"""
            UPDATE invoice.customer
            SET {", ".join(updates)}
            WHERE id = :customer_id AND tenant_id = :tenant_id
            RETURNING
                id, tenant_id, merchant_id, name, email, phone, address,
                telegram_chat_id, telegram_username, telegram_linked_at,
                created_at, updated_at
        """)

        result = db.execute(query, params)
        row = result.fetchone()
        db.commit()

        if not row:
            return None

        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "merchant_id": str(row.merchant_id),
            "name": row.name,
            "email": row.email,
            "phone": row.phone,
            "address": row.address,
            "telegram_chat_id": row.telegram_chat_id,
            "telegram_username": row.telegram_username,
            "telegram_linked_at": row.telegram_linked_at.isoformat() if row.telegram_linked_at else None,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat()
        }

    @staticmethod
    def delete(db: Session, customer_id: UUID, tenant_id: UUID) -> bool:
        """
        Delete customer with tenant isolation.

        Args:
            db: Database session
            customer_id: Customer UUID
            tenant_id: Tenant UUID for isolation

        Returns:
            bool: True if customer was deleted, False if not found
        """
        query = text("""
            DELETE FROM invoice.customer
            WHERE id = :customer_id AND tenant_id = :tenant_id
        """)

        result = db.execute(query, {
            "customer_id": str(customer_id),
            "tenant_id": str(tenant_id)
        })
        db.commit()

        return result.rowcount > 0
