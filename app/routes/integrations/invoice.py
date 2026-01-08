# app/routes/integrations/invoice.py
"""
Invoice API integration routes.

This module provides authenticated endpoints that either:
1. Forward requests to the external Invoice API service (production mode)
2. Use in-memory mock data (mock mode for testing)

All routes require JWT authentication. PDF/Export features can be
tier-gated based on configuration.
"""

from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Response, Query, UploadFile, File, Form
from pydantic import BaseModel
import httpx

from app.core.config import get_settings
from app.routes.auth import get_current_user
from app.core.models import User
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
# Invoice endpoints
# ============================================================================

@router.get("/invoices")
async def list_invoices(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    customer_id: Optional[str] = None,
    status: Optional[str] = None
):
    """List all invoices with optional filtering."""
    if is_mock_mode():
        return mock_svc.list_invoices(limit=limit, skip=skip, customer_id=customer_id, status=status)

    params = {"limit": limit, "skip": skip}
    if customer_id:
        params["customer_id"] = customer_id
    if status:
        params["status"] = status
    return await proxy_request("GET", "/api/invoices", params=params)


@router.post("/invoices")
async def create_invoice(
    data: InvoiceCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new invoice."""
    if is_mock_mode():
        # Validate customer exists
        if not mock_svc.get_customer(data.customer_id):
            raise HTTPException(status_code=400, detail="Customer not found")

        invoice_data = data.model_dump(exclude_none=True)
        # Convert InvoiceItem models to dicts
        if "items" in invoice_data:
            invoice_data["items"] = [
                item.model_dump() if hasattr(item, 'model_dump') else item
                for item in invoice_data["items"]
            ]
        return mock_svc.create_invoice(invoice_data)

    return await proxy_request("POST", "/api/invoices", json_data=data.model_dump(exclude_none=True))


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
        from app.core.database import get_db
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
    current_user: User = Depends(get_current_user)
):
    """Get a specific invoice by ID."""
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
    current_user: User = Depends(get_current_user)
):
    """Update an existing invoice."""
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
    current_user: User = Depends(get_current_user)
):
    """Delete an invoice."""
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

@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    current_user: User = Depends(get_current_user)
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
        from app.core.database import get_db
        db = next(get_db())
        try:
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
        finally:
            db.close()

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
