# app/routes/integrations/invoice.py
"""
Invoice API integration routes.

This module provides authenticated endpoints that either:
1. Forward requests to the external Invoice API service (production mode)
2. Use in-memory mock data (mock mode for testing)

All routes require JWT authentication. PDF/Export features can be
tier-gated based on configuration.
"""

from typing import Optional, Any, List
from fastapi import APIRouter, Depends, HTTPException, Response, Query, UploadFile, File, Form
from pydantic import BaseModel
import httpx
import json
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import get_settings
from app.routes.auth import get_current_user
from app.core.models import User
from app.core.db import get_db
from app.routes.subscriptions import require_pro_tier
from app.services import invoice_mock_service as mock_svc
from app.services.ocr_service import get_ocr_service

router = APIRouter(prefix="/api/integrations/invoice", tags=["invoice-integration"])


# Request/Response Models
class CustomerCreate(BaseModel):
    """Customer creation request."""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    """Customer update request."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


class InvoiceItem(BaseModel):
    """Invoice line item."""
    id: Optional[str] = None
    description: str
    quantity: float = 1
    unit_price: float
    tax_rate: Optional[float] = 0


class InvoiceCreate(BaseModel):
    """Invoice creation request."""
    customer_id: str
    items: list[InvoiceItem]
    due_date: Optional[str] = None
    notes: Optional[str] = None
    discount: Optional[float] = 0
    # Payment verification fields
    bank: Optional[str] = None
    expected_account: Optional[str] = None
    currency: Optional[str] = "KHR"
    recipient_name: Optional[str] = None  # Account holder name on receiving account


class InvoiceUpdate(BaseModel):
    """Invoice update request."""
    items: Optional[list[InvoiceItem]] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None
    discount: Optional[float] = None
    status: Optional[str] = None
    # Payment verification fields
    bank: Optional[str] = None
    expected_account: Optional[str] = None
    currency: Optional[str] = None
    recipient_name: Optional[str] = None  # Account holder name on receiving account


class InvoiceVerify(BaseModel):
    """Invoice verification request."""
    verification_status: str  # pending, verified, rejected
    verified_by: Optional[str] = None
    verification_note: Optional[str] = None


# Helper functions
def is_mock_mode() -> bool:
    """Check if mock mode is enabled."""
    return get_settings().INVOICE_MOCK_MODE


def is_tier_enforced() -> bool:
    """Check if tier enforcement is enabled."""
    return get_settings().INVOICE_TIER_ENFORCEMENT


async def get_invoice_client() -> httpx.AsyncClient:
    """
    Create an authenticated httpx client for the Invoice API.

    Returns:
        Configured AsyncClient with API key header

    Raises:
        HTTPException: If Invoice API is not configured
    """
    settings = get_settings()
    if not settings.INVOICE_API_URL:
        raise HTTPException(
            status_code=503,
            detail="Invoice API not configured. Set INVOICE_API_URL environment variable."
        )

    api_key = settings.INVOICE_API_KEY.get_secret_value()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Invoice API key not configured. Set INVOICE_API_KEY environment variable."
        )

    return httpx.AsyncClient(
        base_url=settings.INVOICE_API_URL,
        headers={"X-API-KEY": api_key},
        timeout=30.0
    )


async def proxy_request(
    method: str,
    path: str,
    json_data: Optional[dict] = None,
    params: Optional[dict] = None
) -> Any:
    """
    Forward a request to the Invoice API.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: API path (e.g., "/api/customers")
        json_data: Request body for POST/PUT
        params: Query parameters

    Returns:
        JSON response from Invoice API

    Raises:
        HTTPException: On API errors
    """
    async with await get_invoice_client() as client:
        try:
            response = await client.request(
                method=method,
                url=path,
                json=json_data,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Forward error from Invoice API
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = e.response.text
            raise HTTPException(
                status_code=e.response.status_code,
                detail=error_detail
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to Invoice API: {str(e)}"
            )


# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Check Invoice API integration health.

    Returns configuration status and mode (mock/production).
    """
    settings = get_settings()

    if is_mock_mode():
        counts = mock_svc.get_data_counts()
        return {
            "configured": True,
            "mode": "mock",
            "url": "mock://in-memory",
            "api_status": "mock_active",
            "mock_data": counts
        }

    configured = bool(settings.INVOICE_API_URL and settings.INVOICE_API_KEY.get_secret_value())

    result = {
        "configured": configured,
        "mode": "production",
        "url": settings.INVOICE_API_URL or "not_set"
    }

    if configured:
        try:
            async with await get_invoice_client() as client:
                response = await client.get("/api/health")
                result["api_status"] = "reachable" if response.status_code == 200 else "error"
        except Exception as e:
            result["api_status"] = f"unreachable: {str(e)}"

    return result


# ============================================================================
# Customer endpoints
# ============================================================================

@router.get("/customers")
async def list_customers(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    search: Optional[str] = None
):
    """List all customers with optional search and pagination."""
    if is_mock_mode():
        return mock_svc.list_customers(limit=limit, skip=skip, search=search)

    params = {"limit": limit, "skip": skip}
    if search:
        params["search"] = search
    return await proxy_request("GET", "/api/customers", params=params)


@router.post("/customers")
async def create_customer(
    data: CustomerCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new customer."""
    if is_mock_mode():
        return mock_svc.create_customer(data.model_dump(exclude_none=True))

    return await proxy_request("POST", "/api/customers", json_data=data.model_dump(exclude_none=True))


@router.get("/customers/{customer_id}")
async def get_customer(
    customer_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific customer by ID."""
    if is_mock_mode():
        customer = mock_svc.get_customer(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer

    return await proxy_request("GET", f"/api/customers/{customer_id}")


@router.put("/customers/{customer_id}")
async def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an existing customer."""
    if is_mock_mode():
        customer = mock_svc.update_customer(customer_id, data.model_dump(exclude_none=True))
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer

    return await proxy_request("PUT", f"/api/customers/{customer_id}", json_data=data.model_dump(exclude_none=True))


@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a customer."""
    if is_mock_mode():
        if not mock_svc.delete_customer(customer_id):
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"status": "deleted", "id": customer_id}

    return await proxy_request("DELETE", f"/api/customers/{customer_id}")


# ============================================================================
# Registered Clients (from Telegram Bot)
# These are clients registered via /register_client bot command.
# They are stored in PostgreSQL invoice.customer table with telegram info.
# ============================================================================

class RegisteredClientResponse(BaseModel):
    """Response model for registered client."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_username: Optional[str] = None
    telegram_linked: bool = False
    telegram_linked_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("/registered-clients")
async def list_registered_clients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    telegram_linked: Optional[bool] = Query(default=None, description="Filter by Telegram linked status")
):
    """
    List clients registered via Telegram bot for the current merchant.

    These are clients created with /register_client command and are scoped
    to the current user (merchant) and their tenant.

    Args:
        limit: Maximum number of results (default 50)
        skip: Offset for pagination
        telegram_linked: Optional filter - True for linked clients only, False for unlinked
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Fetching registered clients for user {current_user.id}, tenant {current_user.tenant_id}")
    try:
        # Build query with tenant + merchant scoping
        query = """
            SELECT
                id, tenant_id, merchant_id, name, email, phone, address,
                telegram_chat_id, telegram_username, telegram_linked_at,
                created_at, updated_at
            FROM invoice.customer
            WHERE tenant_id = :tenant_id
              AND merchant_id = :merchant_id
        """
        params = {
            "tenant_id": str(current_user.tenant_id),
            "merchant_id": str(current_user.id),
            "limit": limit,
            "offset": skip
        }

        # Add telegram_linked filter if specified
        if telegram_linked is True:
            query += " AND telegram_chat_id IS NOT NULL"
        elif telegram_linked is False:
            query += " AND telegram_chat_id IS NULL"

        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"

        result = db.execute(text(query), params)
        rows = result.fetchall()

        clients = []
        for row in rows:
            clients.append({
                "id": str(row.id),
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
            })

        # Get total count for pagination
        count_query = """
            SELECT COUNT(*) FROM invoice.customer
            WHERE tenant_id = :tenant_id AND merchant_id = :merchant_id
        """
        if telegram_linked is True:
            count_query += " AND telegram_chat_id IS NOT NULL"
        elif telegram_linked is False:
            count_query += " AND telegram_chat_id IS NULL"

        count_result = db.execute(text(count_query), {
            "tenant_id": str(current_user.tenant_id),
            "merchant_id": str(current_user.id)
        })
        total = count_result.scalar()

        return {
            "clients": clients,
            "total": total,
            "limit": limit,
            "skip": skip
        }
    except Exception as e:
        logger.error(f"Error fetching registered clients: {e}")
        # Check if it's a column not found error (migration not applied)
        error_str = str(e).lower()
        if "column" in error_str and "does not exist" in error_str:
            raise HTTPException(
                status_code=500,
                detail="Database migration required. The 'merchant_id' column is missing from invoice.customer table. Please apply migration l2g3h4i5j6k7_add_customer_telegram_and_client_linking."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch registered clients: {str(e)}"
        )


@router.get("/registered-clients/check-schema")
async def check_registered_clients_schema(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if the database schema supports registered clients.

    This endpoint verifies that required migrations have been applied.
    """
    import logging
    logger = logging.getLogger(__name__)

    issues = []

    # Check if merchant_id column exists
    try:
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'invoice'
              AND table_name = 'customer'
              AND column_name IN ('merchant_id', 'telegram_chat_id', 'telegram_username', 'telegram_linked_at')
        """))
        columns = [row[0] for row in result.fetchall()]

        required_columns = ['merchant_id', 'telegram_chat_id', 'telegram_username', 'telegram_linked_at']
        missing = [col for col in required_columns if col not in columns]

        if missing:
            issues.append(f"Missing columns in invoice.customer: {missing}")
    except Exception as e:
        issues.append(f"Error checking customer columns: {e}")

    # Check if client_link_code table exists
    try:
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'invoice'
                  AND table_name = 'client_link_code'
            )
        """))
        exists = result.scalar()
        if not exists:
            issues.append("Table invoice.client_link_code does not exist")
    except Exception as e:
        issues.append(f"Error checking client_link_code table: {e}")

    # Check current user info for debugging
    user_info = {
        "user_id": str(current_user.id),
        "tenant_id": str(current_user.tenant_id),
        "username": current_user.username,
        "telegram_linked": current_user.telegram_user_id is not None
    }

    if issues:
        return {
            "status": "migration_required",
            "issues": issues,
            "fix": "Apply migration: alembic upgrade l2g3h4i5j6k7",
            "user_info": user_info
        }

    # Count existing registered clients for this user
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM invoice.customer
            WHERE tenant_id = :tenant_id AND merchant_id = :merchant_id
        """), {
            "tenant_id": str(current_user.tenant_id),
            "merchant_id": str(current_user.id)
        })
        client_count = result.scalar()
    except Exception as e:
        client_count = f"Error: {e}"

    return {
        "status": "ok",
        "schema_valid": True,
        "user_info": user_info,
        "registered_clients_count": client_count
    }


@router.get("/registered-clients/{client_id}")
async def get_registered_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_pending_invoices: bool = Query(default=False, description="Include pending invoices")
):
    """
    Get a specific registered client by ID.

    Validates ownership chain (tenant_id + merchant_id) before returning.

    Args:
        client_id: The client UUID
        include_pending_invoices: If True, includes list of pending invoices for this client
    """
    try:
        # Query with ownership validation
        result = db.execute(
            text("""
                SELECT
                    id, tenant_id, merchant_id, name, email, phone, address,
                    telegram_chat_id, telegram_username, telegram_linked_at,
                    created_at, updated_at
                FROM invoice.customer
                WHERE id = :client_id
                  AND tenant_id = :tenant_id
                  AND merchant_id = :merchant_id
            """),
            {
                "client_id": client_id,
                "tenant_id": str(current_user.tenant_id),
                "merchant_id": str(current_user.id)
            }
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Client not found or access denied"
            )

        client = {
            "id": str(row.id),
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

        # Include pending invoices if requested
        if include_pending_invoices:
            invoices_result = db.execute(
                text("""
                    SELECT
                        id, invoice_number, amount, currency, bank,
                        expected_account, status, verification_status, created_at
                    FROM invoice.invoice
                    WHERE customer_id = :client_id
                      AND verification_status IN ('pending', 'rejected')
                      AND status != 'cancelled'
                    ORDER BY created_at DESC
                    LIMIT 10
                """),
                {"client_id": client_id}
            )
            pending = []
            for inv in invoices_result.fetchall():
                pending.append({
                    "id": str(inv.id),
                    "invoice_number": inv.invoice_number,
                    "amount": float(inv.amount) if inv.amount else 0,
                    "currency": inv.currency or "KHR",
                    "bank": inv.bank,
                    "expected_account": inv.expected_account,
                    "status": inv.status,
                    "verification_status": inv.verification_status,
                    "created_at": inv.created_at.isoformat() if inv.created_at else None
                })
            client["pending_invoices"] = pending

        return client
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch client: {str(e)}"
        )


@router.post("/registered-clients/{client_id}/generate-link")
async def generate_client_link_code(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new Telegram registration link for a client.

    Use this to re-send or regenerate a link for a client who hasn't
    connected their Telegram yet.

    Args:
        client_id: The client UUID
    """
    import secrets

    try:
        # Verify client exists and belongs to this merchant
        client_result = db.execute(
            text("""
                SELECT id, name, telegram_chat_id
                FROM invoice.customer
                WHERE id = :client_id
                  AND tenant_id = :tenant_id
                  AND merchant_id = :merchant_id
            """),
            {
                "client_id": client_id,
                "tenant_id": str(current_user.tenant_id),
                "merchant_id": str(current_user.id)
            }
        )
        client = client_result.fetchone()

        if not client:
            raise HTTPException(
                status_code=404,
                detail="Client not found or access denied"
            )

        if client.telegram_chat_id:
            raise HTTPException(
                status_code=400,
                detail="Client already has Telegram connected"
            )

        # Generate cryptographically secure token (64 chars)
        code = secrets.token_urlsafe(32)

        # Insert new link code
        result = db.execute(
            text("""
                INSERT INTO invoice.client_link_code
                    (tenant_id, merchant_id, customer_id, code)
                VALUES (:tenant_id, :merchant_id, :customer_id, :code)
                RETURNING id, code, expires_at
            """),
            {
                "tenant_id": str(current_user.tenant_id),
                "merchant_id": str(current_user.id),
                "customer_id": client_id,
                "code": code
            }
        )
        db.commit()
        row = result.fetchone()

        # Build Telegram link
        settings = get_settings()
        bot_username = settings.TELEGRAM_BOT_USERNAME or "KS_automations_bot"

        return {
            "client_id": client_id,
            "client_name": client.name,
            "code": row.code,
            "link": f"https://t.me/{bot_username}?start=client_{row.code}",
            "expires_at": row.expires_at.isoformat() if row.expires_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate link code: {str(e)}"
        )


# ============================================================================
# Telegram Invoice Notification Helper
# ============================================================================

async def send_invoice_to_telegram(
    invoice: dict,
    customer: dict,
    db: Session
) -> dict:
    """
    Send invoice notification to client's Telegram.

    Args:
        invoice: The created invoice data
        customer: Customer record with telegram_chat_id
        db: Database session

    Returns:
        Result dict with success status
    """
    settings = get_settings()

    # Check if api-gateway URL is configured
    api_gateway_url = getattr(settings, 'API_GATEWAY_URL', None)
    if not api_gateway_url:
        return {"sent": False, "reason": "API_GATEWAY_URL not configured"}

    telegram_chat_id = customer.get("telegram_chat_id")
    if not telegram_chat_id:
        return {"sent": False, "reason": "Customer has no Telegram linked"}

    # Build notification message
    currency = invoice.get("currency", "KHR")
    amount = invoice.get("total") or invoice.get("amount") or 0

    if currency == "KHR":
        amount_str = f"{amount:,.0f} KHR"
    else:
        amount_str = f"${amount:.2f}"

    # Send via api-gateway internal endpoint
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{api_gateway_url}/internal/telegram/send-invoice",
                json={
                    "chat_id": telegram_chat_id,
                    "invoice_number": invoice.get("invoice_number", "N/A"),
                    "amount": amount_str,
                    "currency": currency,
                    "bank": invoice.get("bank"),
                    "expected_account": invoice.get("expected_account"),
                    "due_date": invoice.get("due_date"),
                    "customer_name": customer.get("name"),
                    "invoice_id": invoice.get("id")
                }
            )
            if response.status_code == 200:
                return {"sent": True, "telegram_chat_id": telegram_chat_id}
            else:
                return {"sent": False, "reason": f"API Gateway returned {response.status_code}"}
    except Exception as e:
        return {"sent": False, "reason": str(e)}


async def get_registered_customer_for_invoice(
    customer_id: str,
    tenant_id: str,
    merchant_id: str,
    db: Session
) -> Optional[dict]:
    """
    Check if customer_id is a registered client with Telegram.

    Args:
        customer_id: Customer UUID
        tenant_id: Tenant UUID for scoping
        merchant_id: Merchant UUID for scoping
        db: Database session

    Returns:
        Customer dict with telegram info, or None if not found
    """
    try:
        result = db.execute(
            text("""
                SELECT
                    id, name, email, phone,
                    telegram_chat_id, telegram_username
                FROM invoice.customer
                WHERE id = :customer_id
                  AND tenant_id = :tenant_id
                  AND merchant_id = :merchant_id
            """),
            {
                "customer_id": customer_id,
                "tenant_id": tenant_id,
                "merchant_id": merchant_id
            }
        )
        row = result.fetchone()
        if row:
            return {
                "id": str(row.id),
                "name": row.name,
                "email": row.email,
                "phone": row.phone,
                "telegram_chat_id": row.telegram_chat_id,
                "telegram_username": row.telegram_username
            }
        return None
    except Exception:
        return None


# ============================================================================
# Invoice endpoints
# ============================================================================

@router.get("/invoices")
async def list_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    customer_id: Optional[str] = None,
    status: Optional[str] = None
):
    """
    List all invoices with optional filtering.

    Returns invoices from both:
    1. PostgreSQL (for registered clients created via Telegram bot)
    2. Mock service or external API (for other customers)
    """
    import logging
    logger = logging.getLogger(__name__)

    all_invoices = []

    # 1. Get PostgreSQL invoices (registered clients)
    try:
        query = """
            SELECT
                i.id, i.tenant_id, i.merchant_id, i.customer_id,
                i.invoice_number, i.amount, i.status, i.items,
                i.currency, i.bank, i.expected_account, i.recipient_name,
                i.due_date, i.verification_status, i.created_at, i.updated_at,
                c.name as customer_name
            FROM invoice.invoice i
            LEFT JOIN invoice.customer c ON i.customer_id = c.id
            WHERE i.tenant_id = :tenant_id AND i.merchant_id = :merchant_id
        """
        params = {
            "tenant_id": str(current_user.tenant_id),
            "merchant_id": str(current_user.id)
        }

        if customer_id:
            query += " AND i.customer_id = :customer_id"
            params["customer_id"] = customer_id
        if status:
            query += " AND i.status = :status"
            params["status"] = status

        query += " ORDER BY i.created_at DESC"

        result = db.execute(text(query), params)
        rows = result.fetchall()

        for row in rows:
            invoice = {
                "id": str(row.id),
                "tenant_id": str(row.tenant_id),
                "customer_id": str(row.customer_id) if row.customer_id else None,
                "customer": {
                    "id": str(row.customer_id) if row.customer_id else None,
                    "name": row.customer_name or "Unknown"
                },
                "invoice_number": row.invoice_number,
                "amount": float(row.amount) if row.amount else 0,
                "total": float(row.amount) if row.amount else 0,
                "status": row.status,
                "items": row.items if row.items else [],
                "currency": row.currency or "KHR",
                "bank": row.bank,
                "expected_account": row.expected_account,
                "recipient_name": row.recipient_name,
                "due_date": row.due_date.isoformat() if row.due_date else None,
                "verification_status": row.verification_status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "source": "registered_client"  # Mark source for debugging
            }
            all_invoices.append(invoice)

        logger.info(f"Found {len(all_invoices)} PostgreSQL invoices for user {current_user.id}")

    except Exception as e:
        logger.error(f"Error fetching PostgreSQL invoices: {e}")
        # Don't fail completely - continue to get mock/external invoices

    # 2. Get mock or external invoices (for non-registered customers)
    try:
        if is_mock_mode():
            mock_invoices = mock_svc.list_invoices(
                limit=limit, skip=skip, customer_id=customer_id, status=status
            )
            if mock_invoices:
                for inv in mock_invoices:
                    inv["source"] = "mock"
                all_invoices.extend(mock_invoices)
        else:
            params = {"limit": limit, "skip": skip}
            if customer_id:
                params["customer_id"] = customer_id
            if status:
                params["status"] = status
            external_invoices = await proxy_request("GET", "/api/invoices", params=params)
            if external_invoices:
                for inv in external_invoices:
                    inv["source"] = "external"
                all_invoices.extend(external_invoices)
    except Exception as e:
        logger.error(f"Error fetching mock/external invoices: {e}")

    # 3. Apply pagination (PostgreSQL invoices first, then others)
    # Sort by created_at descending
    all_invoices.sort(
        key=lambda x: x.get("created_at") or "1970-01-01",
        reverse=True
    )

    # Apply skip and limit
    return all_invoices[skip:skip + limit]


@router.post("/invoices")
async def create_invoice(
    data: InvoiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    send_telegram: bool = Query(default=True, description="Auto-send to client's Telegram if linked")
):
    """
    Create a new invoice.

    If the customer has Telegram linked and send_telegram=True,
    automatically sends invoice notification to their Telegram.

    Args:
        data: Invoice creation data
        send_telegram: Whether to auto-send to Telegram (default True)
    """
    import logging
    import uuid
    from datetime import datetime
    logger = logging.getLogger(__name__)

    # Check if this is a registered client (from Telegram bot)
    registered_customer = await get_registered_customer_for_invoice(
        customer_id=data.customer_id,
        tenant_id=str(current_user.tenant_id),
        merchant_id=str(current_user.id),
        db=db
    )

    telegram_result = None
    invoice = None

    # If this is a registered client, create invoice directly in PostgreSQL
    if registered_customer:
        logger.info(f"Creating invoice for registered client: {registered_customer['name']}")
        try:
            # Calculate totals
            subtotal = sum(
                (item.quantity * item.unit_price) for item in data.items
            )
            tax_total = sum(
                (item.quantity * item.unit_price * (item.tax_rate or 0) / 100) for item in data.items
            )
            discount_amount = subtotal * (data.discount or 0) / 100
            total = subtotal + tax_total - discount_amount

            # Generate invoice number
            result = db.execute(text("""
                SELECT COUNT(*) + 1 FROM invoice.invoice
                WHERE tenant_id = :tenant_id
            """), {"tenant_id": str(current_user.tenant_id)})
            seq = result.scalar() or 1
            invoice_number = f"INV-{datetime.now().strftime('%y%m')}-{seq:05d}"

            # Convert items to JSON
            items_json = [
                {
                    "id": str(uuid.uuid4()),
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "tax_rate": item.tax_rate or 0,
                    "total": item.quantity * item.unit_price
                }
                for item in data.items
            ]

            # Insert invoice
            result = db.execute(
                text("""
                    INSERT INTO invoice.invoice (
                        tenant_id, merchant_id, customer_id, invoice_number,
                        amount, status, items, currency, bank, expected_account,
                        recipient_name, due_date, verification_status, created_at, updated_at
                    ) VALUES (
                        :tenant_id, :merchant_id, :customer_id, :invoice_number,
                        :amount, 'pending', CAST(:items AS jsonb), :currency, :bank, :expected_account,
                        :recipient_name, :due_date, 'pending', NOW(), NOW()
                    )
                    RETURNING id, tenant_id, customer_id, invoice_number, amount, status,
                              items, currency, bank, expected_account, recipient_name, due_date,
                              verification_status, created_at, updated_at
                """),
                {
                    "tenant_id": str(current_user.tenant_id),
                    "merchant_id": str(current_user.id),
                    "customer_id": data.customer_id,
                    "invoice_number": invoice_number,
                    "amount": total,
                    "items": json.dumps(items_json),
                    "currency": data.currency or "KHR",
                    "bank": data.bank,
                    "expected_account": data.expected_account,
                    "recipient_name": data.recipient_name,
                    "due_date": data.due_date
                }
            )
            db.commit()
            row = result.fetchone()

            invoice = {
                "id": str(row.id),
                "tenant_id": str(row.tenant_id),
                "customer_id": str(row.customer_id),
                "customer_name": registered_customer["name"],
                "invoice_number": row.invoice_number,
                "amount": float(row.amount),
                "total": float(row.amount),
                "subtotal": subtotal,
                "tax": tax_total,
                "discount": data.discount or 0,
                "status": row.status,
                "items": items_json,
                "currency": row.currency or "KHR",
                "bank": row.bank,
                "expected_account": row.expected_account,
                "recipient_name": row.recipient_name,
                "due_date": row.due_date.isoformat() if row.due_date else None,
                "verification_status": row.verification_status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            }
            logger.info(f"Invoice created: {invoice_number}")

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating invoice for registered client: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")

    else:
        # Not a registered client - use mock or external API
        if is_mock_mode():
            # Validate customer exists in mock
            if not mock_svc.get_customer(data.customer_id):
                raise HTTPException(status_code=400, detail="Customer not found")

            invoice_data = data.model_dump(exclude_none=True)
            if "items" in invoice_data:
                invoice_data["items"] = [
                    item.model_dump() if hasattr(item, 'model_dump') else item
                    for item in invoice_data["items"]
                ]
            invoice = mock_svc.create_invoice(invoice_data)
        else:
            invoice = await proxy_request("POST", "/api/invoices", json_data=data.model_dump(exclude_none=True))

    # Send to Telegram if customer has it linked
    if send_telegram and registered_customer and registered_customer.get("telegram_chat_id"):
        telegram_result = await send_invoice_to_telegram(
            invoice=invoice,
            customer=registered_customer,
            db=db
        )

    # Include telegram send status in response
    response = dict(invoice) if isinstance(invoice, dict) else invoice
    if telegram_result:
        response["telegram_notification"] = telegram_result

    return response


# ============================================================================
# Export endpoint (must be before parameterized routes)
# ============================================================================

@router.get("/invoices/export")
async def export_invoices(
    current_user: User = Depends(get_current_user),
    format: str = Query(default="csv", pattern="^(csv|xlsx)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Export invoices to CSV or Excel format.

    Requires Pro tier subscription when tier enforcement is enabled.

    Args:
        format: Export format (csv or xlsx)
        start_date: Filter start date (YYYY-MM-DD)
        end_date: Filter end date (YYYY-MM-DD)
    """
    # Check tier enforcement
    if is_tier_enforced():
        from app.routes.subscriptions import has_pro_access, get_or_create_subscription
        from app.core.db import get_db
        db = next(get_db())
        try:
            subscription = get_or_create_subscription(db, current_user)
            if not has_pro_access(subscription):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Pro tier required",
                        "message": "Export is a Pro feature. Please upgrade your subscription.",
                        "upgrade_url": "/dashboard/integrations"
                    }
                )
        finally:
            db.close()

    if is_mock_mode():
        content = mock_svc.export_invoices(format=format, start_date=start_date, end_date=end_date)

        content_type = "text/csv" if format == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"invoices.{format}"

        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    # Production mode - proxy to external API
    params = {"format": format}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    async with await get_invoice_client() as client:
        try:
            response = await client.get("/api/invoices/export", params=params)
            response.raise_for_status()

            content_type = "text/csv" if format == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"invoices.{format}"

            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Failed to export invoices"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to Invoice API: {str(e)}"
            )


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific invoice by ID."""
    # Try PostgreSQL first (for registered client invoices)
    try:
        result = db.execute(
            text("""
                SELECT i.id, i.tenant_id, i.customer_id, i.invoice_number,
                       i.amount, i.status, i.items, i.meta,
                       i.bank, i.expected_account, i.recipient_name, i.due_date, i.currency,
                       i.verification_status, i.verified_at, i.verified_by, i.verification_note,
                       i.created_at, i.updated_at,
                       c.name as customer_name, c.email as customer_email,
                       c.phone as customer_phone
                FROM invoice.invoice i
                LEFT JOIN invoice.customer c ON i.customer_id = c.id
                WHERE i.id = :invoice_id AND i.tenant_id = :tenant_id
            """),
            {"invoice_id": invoice_id, "tenant_id": str(current_user.tenant_id)}
        )
        row = result.fetchone()
        if row:
            return {
                "id": str(row.id),
                "tenant_id": str(row.tenant_id),
                "customer_id": str(row.customer_id) if row.customer_id else None,
                "customer_name": row.customer_name,
                "customer_email": row.customer_email,
                "customer_phone": row.customer_phone,
                "invoice_number": row.invoice_number,
                "amount": float(row.amount) if row.amount else 0,
                "status": row.status or "draft",
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
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            }
    except Exception as e:
        # Log but don't fail - fall through to mock/external
        import logging
        logging.getLogger(__name__).debug(f"PostgreSQL invoice lookup failed: {e}")

    # Fall back to mock/external
    if is_mock_mode():
        invoice = mock_svc.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return invoice

    return await proxy_request("GET", f"/api/invoices/{invoice_id}")


@router.put("/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: str,
    data: InvoiceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing invoice."""
    # 1. Try PostgreSQL first (for registered client invoices)
    try:
        # Prepare items JSON if provided
        items_json = None
        if data.items:
            items_json = json.dumps([
                item.model_dump() if hasattr(item, 'model_dump') else item
                for item in data.items
            ])

        result = db.execute(
            text("""
                UPDATE invoice.invoice
                SET items = COALESCE(CAST(:items AS jsonb), items),
                    due_date = COALESCE(:due_date::date, due_date),
                    status = COALESCE(:status, status),
                    bank = COALESCE(:bank, bank),
                    expected_account = COALESCE(:expected_account, expected_account),
                    recipient_name = COALESCE(:recipient_name, recipient_name),
                    currency = COALESCE(:currency, currency),
                    updated_at = NOW()
                WHERE id = :invoice_id
                  AND tenant_id = :tenant_id
                  AND merchant_id = :merchant_id
                RETURNING id, tenant_id, customer_id, invoice_number, amount, status,
                          items, currency, bank, expected_account, recipient_name, due_date,
                          verification_status, created_at, updated_at
            """),
            {
                "invoice_id": invoice_id,
                "tenant_id": str(current_user.tenant_id),
                "merchant_id": str(current_user.id),
                "items": items_json,
                "due_date": data.due_date,
                "status": data.status,
                "bank": data.bank,
                "expected_account": data.expected_account,
                "recipient_name": data.recipient_name,
                "currency": data.currency
            }
        )
        row = result.fetchone()
        if row:
            db.commit()
            logger.info(f"Updated PostgreSQL invoice {invoice_id}")
            return {
                "id": str(row.id),
                "tenant_id": str(row.tenant_id),
                "customer_id": str(row.customer_id) if row.customer_id else None,
                "invoice_number": row.invoice_number,
                "amount": float(row.amount) if row.amount else 0,
                "total": float(row.amount) if row.amount else 0,
                "status": row.status,
                "items": row.items if row.items else [],
                "currency": row.currency or "KHR",
                "bank": row.bank,
                "expected_account": row.expected_account,
                "recipient_name": row.recipient_name,
                "due_date": row.due_date.isoformat() if row.due_date else None,
                "verification_status": row.verification_status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            }
    except Exception as e:
        logger.error(f"Error updating PostgreSQL invoice: {e}")
        db.rollback()

    # 2. Fall back to mock or external API
    if is_mock_mode():
        update_data = data.model_dump(exclude_none=True)
        # Convert InvoiceItem models to dicts
        if "items" in update_data and update_data["items"]:
            update_data["items"] = [
                item.model_dump() if hasattr(item, 'model_dump') else item
                for item in update_data["items"]
            ]
        invoice = mock_svc.update_invoice(invoice_id, update_data)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return invoice

    return await proxy_request("PUT", f"/api/invoices/{invoice_id}", json_data=data.model_dump(exclude_none=True))


@router.delete("/invoices/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an invoice."""
    # Try PostgreSQL first (for registered client invoices)
    try:
        result = db.execute(
            text("""
                DELETE FROM invoice.invoice
                WHERE id = :invoice_id AND tenant_id = :tenant_id
                RETURNING id
            """),
            {"invoice_id": invoice_id, "tenant_id": str(current_user.tenant_id)}
        )
        deleted = result.fetchone()
        if deleted:
            db.commit()
            return {"status": "deleted", "id": invoice_id}
    except Exception as e:
        db.rollback()
        import logging
        logging.getLogger(__name__).debug(f"PostgreSQL invoice delete failed: {e}")

    # Fall back to mock/external
    if is_mock_mode():
        if not mock_svc.delete_invoice(invoice_id):
            raise HTTPException(status_code=404, detail="Invoice not found")
        return {"status": "deleted", "id": invoice_id}

    return await proxy_request("DELETE", f"/api/invoices/{invoice_id}")


# ============================================================================
# Invoice verification endpoint
# ============================================================================

@router.patch("/invoices/{invoice_id}/verify")
async def verify_invoice(
    invoice_id: str,
    data: InvoiceVerify,
    current_user: User = Depends(get_current_user)
):
    """
    Update verification status of an invoice.

    Used by OCR verification service to mark invoices as verified/rejected.

    Args:
        invoice_id: The invoice ID to verify
        data: Verification data including status, verifiedBy, and optional note
    """
    # Validate verification_status
    valid_statuses = ["pending", "verified", "rejected"]
    if data.verification_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid verification_status. Must be one of: {valid_statuses}"
        )

    if is_mock_mode():
        invoice = mock_svc.verify_invoice(invoice_id, data.model_dump(exclude_none=True))
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return invoice

    return await proxy_request(
        "PATCH",
        f"/api/invoices/{invoice_id}/verify",
        json_data=data.model_dump(exclude_none=True)
    )


# ============================================================================
# Screenshot OCR verification endpoint
# ============================================================================

@router.post("/invoices/{invoice_id}/screenshot")
async def upload_invoice_screenshot(
    invoice_id: str,
    image: UploadFile = File(..., description="Payment screenshot image"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a payment screenshot for OCR verification.

    This endpoint:
    1. Retrieves the invoice to get expected payment details
    2. Sends the screenshot to OCR service for verification
    3. Updates the invoice verification status based on OCR result

    Args:
        invoice_id: The invoice ID to verify payment for
        image: The payment screenshot image file
    """
    ocr_service = get_ocr_service()

    if not ocr_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="OCR service not configured. Set OCR_API_URL and OCR_API_KEY."
        )

    # Get the invoice to build expected payment
    if is_mock_mode():
        invoice = mock_svc.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
    else:
        invoice = await proxy_request("GET", f"/api/invoices/{invoice_id}")

    # Build expected payment from invoice
    expected_payment = {
        "amount": invoice.get("total"),
        "currency": invoice.get("currency", "KHR"),
        "toAccount": invoice.get("expected_account"),
        "bank": invoice.get("bank"),
        "recipientName": invoice.get("recipient_name"),
        "dueDate": invoice.get("due_date"),
        "tolerancePercent": 5
    }

    # Read image data
    image_data = await image.read()
    if not image_data:
        raise HTTPException(status_code=400, detail="Empty image file")

    # Send to OCR service
    ocr_result = await ocr_service.verify_screenshot(
        image_data=image_data,
        filename=image.filename or "screenshot.jpg",
        invoice_id=invoice_id,
        expected_payment=expected_payment,
        customer_id=invoice.get("customer_id")
    )

    # Check if OCR succeeded
    if ocr_result.get("success") is False:
        return {
            "success": False,
            "invoice_id": invoice_id,
            "ocr_result": ocr_result,
            "message": ocr_result.get("message", "OCR verification failed")
        }

    # Extract verification status from OCR result
    verification = ocr_result.get("verification", {})
    verification_status = verification.get("status", "pending")

    # Map OCR status to invoice verification status
    if verification_status == "verified":
        invoice_verification_status = "verified"
    elif verification_status == "rejected":
        invoice_verification_status = "rejected"
    else:
        invoice_verification_status = "pending"

    # Update invoice with verification result
    verify_data = {
        "verification_status": invoice_verification_status,
        "verified_by": "ocr-verification-service",
        "verification_note": f"OCR Record: {ocr_result.get('recordId', 'N/A')}. {verification.get('rejectionReason', '')}"
    }

    if is_mock_mode():
        updated_invoice = mock_svc.verify_invoice(invoice_id, verify_data)
    else:
        updated_invoice = await proxy_request(
            "PATCH",
            f"/api/invoices/{invoice_id}/verify",
            json_data=verify_data
        )

    return {
        "success": True,
        "invoice_id": invoice_id,
        "verification_status": invoice_verification_status,
        "ocr_result": ocr_result,
        "invoice": updated_invoice
    }


@router.post("/verify-screenshot")
async def verify_standalone_screenshot(
    image: UploadFile = File(..., description="Payment screenshot image"),
    invoice_id: Optional[str] = Form(None, description="Optional invoice ID"),
    expected_amount: Optional[float] = Form(None, description="Expected payment amount"),
    expected_currency: Optional[str] = Form(None, description="Expected currency (KHR/USD)"),
    expected_account: Optional[str] = Form(None, description="Expected recipient account"),
    current_user: User = Depends(get_current_user)
):
    """
    Verify a payment screenshot without requiring an invoice.

    Use this for standalone screenshot verification or when you want to
    manually specify expected payment details.

    Args:
        image: The payment screenshot image file
        invoice_id: Optional invoice ID to link the verification
        expected_amount: Expected payment amount
        expected_currency: Expected currency code (default: KHR)
        expected_account: Expected recipient account number
    """
    ocr_service = get_ocr_service()

    if not ocr_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="OCR service not configured. Set OCR_API_URL and OCR_API_KEY."
        )

    # Read image data
    image_data = await image.read()
    if not image_data:
        raise HTTPException(status_code=400, detail="Empty image file")

    # Build expected payment if provided
    expected_payment = None
    if expected_amount is not None or expected_currency or expected_account:
        expected_payment = {}
        if expected_amount is not None:
            expected_payment["amount"] = expected_amount
        if expected_currency:
            expected_payment["currency"] = expected_currency
        if expected_account:
            expected_payment["toAccount"] = expected_account

    # Send to OCR service
    ocr_result = await ocr_service.verify_screenshot(
        image_data=image_data,
        filename=image.filename or "screenshot.jpg",
        invoice_id=invoice_id,
        expected_payment=expected_payment
    )

    return {
        "success": ocr_result.get("success", True) if "error" not in ocr_result else False,
        "invoice_id": invoice_id,
        "ocr_result": ocr_result
    }


# ============================================================================
# PDF download endpoint
# ============================================================================

def generate_pdf_from_invoice(invoice: dict) -> bytes:
    """Generate a PDF from invoice data."""
    invoice_num = invoice.get("invoice_number", "N/A")
    customer_name = invoice.get("customer", {}).get("name") if isinstance(invoice.get("customer"), dict) else invoice.get("customer_name", "Unknown")
    total = invoice.get("total") or invoice.get("amount") or 0
    currency = invoice.get("currency", "KHR")
    bank = invoice.get("bank") or "N/A"
    expected_account = invoice.get("expected_account") or "N/A"
    recipient_name = invoice.get("recipient_name") or "N/A"
    verification_status = (invoice.get("verification_status") or "pending").upper()
    status = invoice.get("status", "draft")
    due_date = invoice.get("due_date") or "N/A"

    # Format amount with currency
    if currency == "KHR":
        amount_str = f"{float(total):,.0f} KHR"
    else:
        amount_str = f"${float(total):.2f} {currency}"

    # Verification badge
    if verification_status == "VERIFIED":
        badge = "[VERIFIED]"
    elif verification_status == "REJECTED":
        badge = "[REJECTED]"
    else:
        badge = "[PENDING]"

    # Build PDF content
    content = f"""Invoice: {invoice_num}
Customer: {customer_name}
Total: {amount_str}
Status: {status}
Due Date: {due_date}
Verification: {badge}

Payment Information:
Bank: {bank}
Account: {expected_account}
Recipient: {recipient_name}
Amount: {amount_str}

Generated by Invoice System"""

    # Minimal valid PDF structure
    pdf_content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {len(content) + 100} >>
stream
BT
/F1 12 Tf
50 742 Td
"""
    # Add each line of content
    y_pos = 742
    for line in content.split('\n'):
        safe_line = line.replace('(', '\\(').replace(')', '\\)')
        pdf_content += f"({safe_line}) Tj\n0 -16 Td\n"
        y_pos -= 16

    pdf_content += """ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
0
%%EOF"""

    return pdf_content.encode('latin-1')


@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download invoice as PDF.

    Returns the PDF file directly as binary content.
    Requires Pro tier subscription when tier enforcement is enabled.
    """
    # Check tier enforcement
    if is_tier_enforced():
        # Manually check Pro tier (can't use Depends conditionally)
        from app.routes.subscriptions import has_pro_access, get_or_create_subscription
        subscription = get_or_create_subscription(db, current_user)
        if not has_pro_access(subscription):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Pro tier required",
                    "message": "PDF download is a Pro feature. Please upgrade your subscription.",
                    "upgrade_url": "/dashboard/integrations"
                }
            )

    # 1. Try PostgreSQL first (for registered client invoices)
    try:
        result = db.execute(
            text("""
                SELECT i.id, i.invoice_number, i.amount, i.status, i.currency,
                       i.bank, i.expected_account, i.recipient_name, i.due_date,
                       i.verification_status, c.name as customer_name
                FROM invoice.invoice i
                LEFT JOIN invoice.customer c ON i.customer_id = c.id
                WHERE i.id = :invoice_id
                  AND i.tenant_id = :tenant_id
                  AND i.merchant_id = :merchant_id
            """),
            {
                "invoice_id": invoice_id,
                "tenant_id": str(current_user.tenant_id),
                "merchant_id": str(current_user.id)
            }
        )
        row = result.fetchone()
        if row:
            invoice = {
                "invoice_number": row.invoice_number,
                "amount": float(row.amount) if row.amount else 0,
                "total": float(row.amount) if row.amount else 0,
                "status": row.status,
                "currency": row.currency or "KHR",
                "bank": row.bank,
                "expected_account": row.expected_account,
                "recipient_name": row.recipient_name,
                "due_date": row.due_date.isoformat() if row.due_date else None,
                "verification_status": row.verification_status,
                "customer_name": row.customer_name or "Unknown"
            }
            pdf_content = generate_pdf_from_invoice(invoice)
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=invoice-{row.invoice_number}.pdf"
                }
            )
    except Exception as e:
        logger.error(f"Error generating PostgreSQL invoice PDF: {e}")

    # 2. Fall back to mock mode
    if is_mock_mode():
        pdf_content = mock_svc.generate_pdf(invoice_id)
        if not pdf_content:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=invoice-{invoice_id}.pdf"
            }
        )

    # Production mode - proxy to external API
    async with await get_invoice_client() as client:
        try:
            response = await client.get(f"/api/invoices/{invoice_id}/pdf")
            response.raise_for_status()

            return Response(
                content=response.content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=invoice-{invoice_id}.pdf"
                }
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail="Failed to generate PDF"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to Invoice API: {str(e)}"
            )


# ============================================================================
# Send Invoice to Customer (Telegram)
# ============================================================================

@router.post("/invoices/{invoice_id}/send")
async def send_invoice_to_customer(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send or resend an invoice notification to the customer's Telegram.

    This endpoint allows you to manually send an invoice notification
    to a customer who has Telegram linked. Useful for:
    - Resending notifications if the customer missed it
    - Sending after updating invoice details
    - Following up on pending payments

    Returns:
        Success status and telegram notification result
    """
    import logging
    logger = logging.getLogger(__name__)

    # Get the invoice from PostgreSQL
    try:
        result = db.execute(
            text("""
                SELECT i.id, i.tenant_id, i.customer_id, i.invoice_number,
                       i.amount, i.status, i.currency, i.bank, i.expected_account,
                       i.recipient_name, i.due_date, i.verification_status, i.created_at,
                       c.name as customer_name, c.email as customer_email,
                       c.telegram_chat_id, c.telegram_username
                FROM invoice.invoice i
                LEFT JOIN invoice.customer c ON i.customer_id = c.id
                WHERE i.id = :invoice_id AND i.tenant_id = :tenant_id
            """),
            {"invoice_id": invoice_id, "tenant_id": str(current_user.tenant_id)}
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Invoice not found")

        if not row.telegram_chat_id:
            raise HTTPException(
                status_code=400,
                detail="Customer does not have Telegram linked. Cannot send notification."
            )

        # Build invoice data for notification
        invoice_data = {
            "id": str(row.id),
            "invoice_number": row.invoice_number,
            "total": float(row.amount) if row.amount else 0,
            "amount": float(row.amount) if row.amount else 0,
            "currency": row.currency or "KHR",
            "bank": row.bank,
            "expected_account": row.expected_account,
            "recipient_name": row.recipient_name,
            "due_date": row.due_date.isoformat() if row.due_date else None,
            "status": row.status,
            "verification_status": row.verification_status
        }

        customer_data = {
            "id": str(row.customer_id),
            "name": row.customer_name,
            "email": row.customer_email,
            "telegram_chat_id": row.telegram_chat_id,
            "telegram_username": row.telegram_username
        }

        # Send to Telegram
        telegram_result = await send_invoice_to_telegram(
            invoice=invoice_data,
            customer=customer_data,
            db=db
        )

        if telegram_result.get("sent"):
            logger.info(f"Invoice {row.invoice_number} sent to Telegram chat {row.telegram_chat_id}")
            return {
                "success": True,
                "message": f"Invoice sent to {row.customer_name}'s Telegram",
                "invoice_number": row.invoice_number,
                "telegram_username": row.telegram_username,
                "telegram_result": telegram_result
            }
        else:
            logger.warning(f"Failed to send invoice to Telegram: {telegram_result.get('reason')}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send Telegram notification: {telegram_result.get('reason', 'Unknown error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending invoice to customer: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send invoice: {str(e)}"
        )


# ============================================================================
# Statistics endpoint
# ============================================================================

@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user)
):
    """Get invoice statistics and dashboard data."""
    if is_mock_mode():
        return mock_svc.get_stats()

    return await proxy_request("GET", "/api/stats")


# ============================================================================
# Admin/Debug endpoints (for testing)
# ============================================================================

@router.post("/admin/seed")
async def seed_sample_data(
    current_user: User = Depends(get_current_user)
):
    """
    Seed sample data for testing (mock mode only).

    Only works when INVOICE_MOCK_MODE is enabled.
    """
    if not is_mock_mode():
        raise HTTPException(
            status_code=400,
            detail="Seed endpoint only available in mock mode. Set INVOICE_MOCK_MODE=true"
        )

    return mock_svc.seed_sample_data()


@router.post("/admin/clear")
async def clear_all_data(
    current_user: User = Depends(get_current_user)
):
    """
    Clear all mock data (mock mode only).

    Only works when INVOICE_MOCK_MODE is enabled.
    """
    if not is_mock_mode():
        raise HTTPException(
            status_code=400,
            detail="Clear endpoint only available in mock mode. Set INVOICE_MOCK_MODE=true"
        )

    return mock_svc.clear_all_data()
