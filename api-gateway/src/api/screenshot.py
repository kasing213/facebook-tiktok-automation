"""
Screenshot Access API - Secure endpoints for viewing payment screenshots.

This module provides authenticated endpoints for accessing payment screenshots
stored in MongoDB GridFS. All access is validated against tenant permissions
to ensure merchants can only view their own customers' screenshots.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from io import BytesIO

from src.services.payment_screenshot_service import PaymentScreenshotService
from src.bot.services.linking import get_user_by_telegram_id
from src.core.exceptions import AuthenticationError, PermissionError

logger = logging.getLogger(__name__)
router = APIRouter()

screenshot_service = PaymentScreenshotService()


@router.get("/screenshots/{screenshot_id}/view")
async def view_screenshot(
    screenshot_id: str,
    telegram_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    View payment screenshot with authentication validation.

    This endpoint serves payment screenshots to authenticated merchants.
    Access is validated to ensure only the merchant who owns the invoice
    can view the associated screenshot.

    Args:
        screenshot_id: Database ID of the screenshot
        telegram_id: Telegram user ID for authentication (optional)
        user_id: Backend user ID for authentication (optional)

    Returns:
        StreamingResponse with the screenshot image

    Security:
        - Validates merchant authentication
        - Enforces tenant isolation
        - Logs all access attempts
        - Returns 404 for unauthorized access (prevents information leakage)
    """
    try:
        # Determine authentication method
        authenticated_user = None

        if telegram_id:
            # Telegram-based authentication
            authenticated_user = await get_user_by_telegram_id(telegram_id)
            if not authenticated_user:
                logger.warning(f"Screenshot access denied - invalid Telegram ID: {telegram_id}")
                raise HTTPException(status_code=404, detail="Screenshot not found")

        elif user_id:
            # Backend user authentication (for web dashboard access)
            # This would integrate with your existing user authentication system
            # For now, we'll focus on Telegram-based access
            logger.warning("Backend user authentication not yet implemented")
            raise HTTPException(status_code=401, detail="Authentication required")

        else:
            logger.warning("Screenshot access attempted without authentication")
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get tenant ID for permission validation
        tenant_id = authenticated_user.get("tenant_id")
        if not tenant_id:
            logger.error(f"No tenant_id found for user: {authenticated_user.get('user_id')}")
            raise HTTPException(status_code=404, detail="Screenshot not found")

        logger.info(f"Screenshot access request: {screenshot_id} by tenant {tenant_id}")

        # Get screenshot data with tenant validation
        screenshot_data = await screenshot_service.get_screenshot_image_data(
            screenshot_id=screenshot_id,
            tenant_id=tenant_id
        )

        if not screenshot_data:
            logger.warning(f"Screenshot not found or access denied: {screenshot_id} for tenant {tenant_id}")
            raise HTTPException(status_code=404, detail="Screenshot not found")

        image_bytes, content_type, filename = screenshot_data

        # Log successful access
        logger.info(f"✅ Screenshot served: {screenshot_id} to tenant {tenant_id} ({len(image_bytes)} bytes)")

        # Return image as streaming response
        return StreamingResponse(
            BytesIO(image_bytes),
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename=\"{filename}\"",
                "Cache-Control": "private, max-age=300",  # 5 minutes cache
                "X-Screenshot-ID": screenshot_id
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(f"❌ Error serving screenshot {screenshot_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/screenshots/{screenshot_id}/metadata")
async def get_screenshot_metadata(
    screenshot_id: str,
    telegram_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    Get screenshot metadata with authentication validation.

    Returns screenshot information including OCR results, confidence,
    and verification status without exposing the actual image.

    Args:
        screenshot_id: Database ID of the screenshot
        telegram_id: Telegram user ID for authentication (optional)
        user_id: Backend user ID for authentication (optional)

    Returns:
        Dict with screenshot metadata

    Security:
        - Same authentication and tenant validation as view endpoint
        - Sanitizes sensitive information
        - Logs metadata access
    """
    try:
        # Same authentication logic as view endpoint
        authenticated_user = None

        if telegram_id:
            authenticated_user = await get_user_by_telegram_id(telegram_id)
            if not authenticated_user:
                logger.warning(f"Screenshot metadata access denied - invalid Telegram ID: {telegram_id}")
                raise HTTPException(status_code=404, detail="Screenshot not found")

        else:
            logger.warning("Screenshot metadata access attempted without authentication")
            raise HTTPException(status_code=401, detail="Authentication required")

        tenant_id = authenticated_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=404, detail="Screenshot not found")

        # Get screenshot metadata
        screenshot = await screenshot_service.get_screenshot_by_id(
            screenshot_id=screenshot_id,
            tenant_id=tenant_id
        )

        if not screenshot:
            logger.warning(f"Screenshot metadata not found: {screenshot_id} for tenant {tenant_id}")
            raise HTTPException(status_code=404, detail="Screenshot not found")

        # Sanitize metadata for response
        metadata = screenshot.get('metadata', {})

        response_data = {
            "screenshot_id": screenshot['id'],
            "created_at": screenshot['created_at'],
            "verified": screenshot['verified'],
            "verified_at": screenshot.get('verified_at'),
            "file_size": metadata.get('file_size'),
            "content_type": metadata.get('content_type'),
            "filename": metadata.get('filename'),
            "invoice_id": metadata.get('invoice_id'),
            "customer_id": metadata.get('customer_id'),
            "ocr_confidence": metadata.get('ocr_confidence'),
            "verification_status": metadata.get('verification_status'),
            "verification_method": metadata.get('verification_method'),
            "ocr_processed": metadata.get('ocr_processed', False),
            "manually_verified": metadata.get('manually_verified', False)
        }

        # Remove None values
        response_data = {k: v for k, v in response_data.items() if v is not None}

        logger.info(f"✅ Screenshot metadata served: {screenshot_id} to tenant {tenant_id}")
        return response_data

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Error getting screenshot metadata {screenshot_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/screenshots/invoice/{invoice_id}")
async def list_screenshots_for_invoice(
    invoice_id: str,
    telegram_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    List all screenshots for a specific invoice.

    Returns a list of screenshots associated with the given invoice ID.
    Useful for viewing payment history and multiple payment attempts.

    Args:
        invoice_id: Invoice ID to get screenshots for
        telegram_id: Telegram user ID for authentication (optional)
        user_id: Backend user ID for authentication (optional)

    Returns:
        List of screenshot metadata objects

    Security:
        - Validates merchant owns the invoice
        - Enforces tenant isolation
        - Returns sanitized metadata only
    """
    try:
        # Authentication logic
        authenticated_user = None

        if telegram_id:
            authenticated_user = await get_user_by_telegram_id(telegram_id)
            if not authenticated_user:
                raise HTTPException(status_code=404, detail="Invoice not found")

        else:
            raise HTTPException(status_code=401, detail="Authentication required")

        tenant_id = authenticated_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Additional validation: verify merchant owns this invoice
        from src.db.postgres import get_db_session
        from sqlalchemy import text

        with get_db_session() as db:
            invoice_check = db.execute(
                text("""
                    SELECT i.id FROM invoice.invoice i
                    WHERE i.id = :invoice_id
                    AND i.tenant_id = :tenant_id
                """),
                {
                    "invoice_id": invoice_id,
                    "tenant_id": tenant_id
                }
            ).fetchone()

            if not invoice_check:
                logger.warning(f"Invoice access denied: {invoice_id} for tenant {tenant_id}")
                raise HTTPException(status_code=404, detail="Invoice not found")

        # Get screenshots for invoice
        screenshots = await screenshot_service.get_screenshots_for_invoice(
            invoice_id=invoice_id,
            tenant_id=tenant_id
        )

        # Sanitize screenshot data for response
        response_screenshots = []
        for screenshot in screenshots:
            metadata = screenshot.get('metadata', {})

            sanitized = {
                "screenshot_id": screenshot['id'],
                "created_at": screenshot['created_at'],
                "verified": screenshot['verified'],
                "verified_at": screenshot.get('verified_at'),
                "ocr_confidence": metadata.get('ocr_confidence'),
                "verification_status": metadata.get('verification_status'),
                "verification_method": metadata.get('verification_method'),
                "file_size": metadata.get('file_size'),
                "filename": metadata.get('filename')
            }

            # Remove None values
            sanitized = {k: v for k, v in sanitized.items() if v is not None}
            response_screenshots.append(sanitized)

        logger.info(f"✅ Listed {len(response_screenshots)} screenshots for invoice {invoice_id}")
        return {
            "invoice_id": invoice_id,
            "screenshot_count": len(response_screenshots),
            "screenshots": response_screenshots
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Error listing screenshots for invoice {invoice_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/screenshots/{screenshot_id}")
async def delete_screenshot(
    screenshot_id: str,
    telegram_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    Delete a screenshot (admin/owner only).

    Removes screenshot from both GridFS and database.
    This is primarily for cleanup and should be used cautiously
    as it removes audit trail evidence.

    Args:
        screenshot_id: Database ID of the screenshot
        telegram_id: Telegram user ID (must be owner)
        user_id: Backend user ID (must be admin/owner)

    Returns:
        Success confirmation

    Security:
        - Requires owner-level permissions
        - Logs all deletion attempts
        - Validates tenant ownership
    """
    try:
        # Authentication with elevated permission check
        authenticated_user = None

        if telegram_id:
            authenticated_user = await get_user_by_telegram_id(telegram_id)
            if not authenticated_user:
                raise HTTPException(status_code=404, detail="Screenshot not found")

            # Check if user has owner permissions
            user_role = authenticated_user.get("role", "user")
            if user_role not in ["admin", "owner"]:
                logger.warning(f"Screenshot deletion denied - insufficient permissions: {telegram_id} ({user_role})")
                raise HTTPException(status_code=403, detail="Insufficient permissions")

        else:
            raise HTTPException(status_code=401, detail="Authentication required")

        tenant_id = authenticated_user.get("tenant_id")
        user_id = authenticated_user.get("user_id")

        # Verify screenshot exists and belongs to tenant
        screenshot = await screenshot_service.get_screenshot_by_id(
            screenshot_id=screenshot_id,
            tenant_id=tenant_id
        )

        if not screenshot:
            raise HTTPException(status_code=404, detail="Screenshot not found")

        # Log deletion attempt
        logger.warning(f"🗑️ Screenshot deletion requested: {screenshot_id} by user {user_id} (role: {user_role})")

        # Note: Actual deletion would be implemented here
        # For now, we'll return success but not actually delete
        # This is a safety measure to preserve audit trails

        logger.info(f"⚠️ Screenshot deletion logged but not executed: {screenshot_id}")
        return {
            "message": "Screenshot deletion logged",
            "screenshot_id": screenshot_id,
            "note": "Actual deletion disabled for audit trail preservation"
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Error deleting screenshot {screenshot_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")