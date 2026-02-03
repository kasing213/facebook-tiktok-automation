# api-gateway/src/api/ocr.py
"""OCR Verification API routes."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends

from src.services.ocr_service import ocr_service
from src.middleware.service_auth import require_service_jwt

router = APIRouter()


@router.get("/health")
async def health():
    """OCR service health check."""
    return await ocr_service.health_check()


@router.get("/status")
async def status():
    """Get detailed OCR service status."""
    return await ocr_service.get_status()


@router.post("/verify", dependencies=[Depends(require_service_jwt)])
async def verify_screenshot(
    image: UploadFile = File(..., description="Payment screenshot image"),
    invoice_id: Optional[str] = Form(None, description="Invoice ID to lookup expected payment"),
    customer_id: Optional[str] = Form(None, description="Customer reference ID"),
    expected_amount: Optional[float] = Form(None, description="Expected payment amount"),
    expected_currency: Optional[str] = Form(None, description="Expected currency code"),
    service_context: Dict[str, Any] = Depends(require_service_jwt),
):
    """
    Verify a payment screenshot using OCR.

    Send a screenshot image to the OCR service for verification.
    Optionally include invoice_id or expected payment details for validation.
    """
    if not ocr_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="OCR service not configured. Set OCR_API_URL and OCR_API_KEY."
        )

    # Read image data
    image_data = await image.read()

    if not image_data:
        raise HTTPException(status_code=400, detail="Empty image file")

    # Build expected payment dict if provided
    expected_payment = None
    if expected_amount is not None or expected_currency is not None:
        expected_payment = {}
        if expected_amount is not None:
            expected_payment["amount"] = expected_amount
        if expected_currency is not None:
            expected_payment["currency"] = expected_currency

    result = await ocr_service.verify_screenshot(
        image_data=image_data,
        filename=image.filename or "screenshot.jpg",
        invoice_id=invoice_id,
        expected_payment=expected_payment,
        customer_id=customer_id
    )

    return result


@router.get("/verify/{record_id}", dependencies=[Depends(require_service_jwt)])
async def get_verification(record_id: str, service_context: Dict[str, Any] = Depends(require_service_jwt)):
    """
    Get verification result by record ID.

    Retrieve a previously processed verification result.
    """
    if not ocr_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="OCR service not configured"
        )

    return await ocr_service.get_verification(record_id)
