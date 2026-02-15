"""
Payment Screenshot Service - Handles payment screenshot storage and retrieval.

This service manages payment screenshots using MongoDB GridFS (reusing existing infrastructure)
and maintains metadata in the scriptclient.screenshot table. It provides secure access
to screenshots for manual verification by merchants via Telegram.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID

# Database imports
from src.db.postgres import get_db_session
from sqlalchemy import text

# Reuse existing GridFS storage service
try:
    # Import from main backend where GridFS is implemented
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../app'))
    from app.services.ads_alert_service import GridFSStorageService
    GRIDFS_AVAILABLE = True
except ImportError:
    GRIDFS_AVAILABLE = False

logger = logging.getLogger(__name__)


class PaymentScreenshotService:
    """
    Service for managing payment screenshots using MongoDB GridFS.

    Features:
    - Store screenshots with tenant isolation
    - Link screenshots to invoices and customers
    - Provide secure access for manual verification
    - Automatic cleanup of old screenshots
    """

    def __init__(self):
        if GRIDFS_AVAILABLE:
            self._storage = GridFSStorageService()
        else:
            self._storage = None
            logger.warning("GridFS storage not available - using mock mode")

    def _is_storage_available(self) -> bool:
        """Check if GridFS storage is properly configured"""
        return self._storage is not None and self._storage._is_configured()

    async def save_screenshot(
        self,
        image_data: bytes,
        invoice_id: str,
        customer_id: str,
        tenant_id: str,
        filename: str = None
    ) -> Dict[str, Any]:
        """
        Save payment screenshot to GridFS and create database record.

        Args:
            image_data: Screenshot image bytes
            invoice_id: Associated invoice ID
            customer_id: Associated customer ID
            tenant_id: Tenant ID for isolation
            filename: Original filename (optional)

        Returns:
            Dict with screenshot metadata including database ID and GridFS file ID
        """
        try:
            # Generate unique filename if not provided
            if not filename:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                filename = f"payment_{invoice_id[:8]}_{timestamp}.jpg"

            # Store in GridFS
            if self._is_storage_available():
                gridfs_file_id, download_url = await self._storage.upload_file(
                    tenant_id=UUID(tenant_id),
                    file_content=image_data,
                    filename=filename,
                    content_type="image/jpeg"
                )
                logger.info(f"Uploaded screenshot to GridFS: {gridfs_file_id}")
            else:
                # Mock mode for development
                gridfs_file_id = str(uuid.uuid4())
                download_url = f"/api/gateway/screenshots/{gridfs_file_id}/view"
                logger.warning("GridFS not available - using mock storage")

            # Create database record in scriptclient.screenshot table
            screenshot_id = await self._create_screenshot_record(
                tenant_id=tenant_id,
                invoice_id=invoice_id,
                customer_id=customer_id,
                gridfs_file_id=gridfs_file_id,
                download_url=download_url,
                filename=filename,
                file_size=len(image_data)
            )

            return {
                'id': screenshot_id,
                'gridfs_file_id': gridfs_file_id,
                'download_url': download_url,
                'filename': filename,
                'file_size': len(image_data),
                'created_at': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
            raise

    async def _create_screenshot_record(
        self,
        tenant_id: str,
        invoice_id: str,
        customer_id: str,
        gridfs_file_id: str,
        download_url: str,
        filename: str,
        file_size: int
    ) -> str:
        """Create record in scriptclient.screenshot table"""

        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        INSERT INTO scriptclient.screenshot
                        (tenant_id, file_path, file_url, verified, meta, created_at, updated_at)
                        VALUES
                        (:tenant_id, :file_path, :file_url, false, :meta, NOW(), NOW())
                        RETURNING id
                    """),
                    {
                        "tenant_id": tenant_id,
                        "file_path": gridfs_file_id,  # Store GridFS file ID in file_path
                        "file_url": download_url,
                        "meta": {
                            "invoice_id": invoice_id,
                            "customer_id": customer_id,
                            "filename": filename,
                            "file_size": file_size,
                            "content_type": "image/jpeg",
                            "verification_status": "pending",
                            "ocr_processed": False
                        }
                    }
                )

                screenshot_id = result.fetchone()[0]
                db.commit()

                logger.info(f"Created screenshot record: {screenshot_id}")
                return str(screenshot_id)

        except Exception as e:
            logger.error(f"Error creating screenshot record: {e}")
            raise

    async def update_ocr_results(
        self,
        screenshot_id: str,
        confidence: float,
        status: str,
        ocr_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update screenshot record with OCR processing results.

        Args:
            screenshot_id: Database screenshot ID
            confidence: OCR confidence score (0.0-1.0)
            status: OCR verification status
            ocr_data: Additional OCR extracted data

        Returns:
            True if updated successfully
        """
        try:
            with get_db_session() as db:
                # Get current metadata
                current_result = db.execute(
                    text("SELECT meta FROM scriptclient.screenshot WHERE id = :id"),
                    {"id": screenshot_id}
                ).fetchone()

                if not current_result:
                    logger.error(f"Screenshot not found: {screenshot_id}")
                    return False

                current_meta = current_result.meta or {}

                # Update metadata with OCR results
                updated_meta = {
                    **current_meta,
                    "ocr_processed": True,
                    "ocr_confidence": float(confidence),
                    "verification_status": status,
                    "ocr_processed_at": datetime.now(timezone.utc).isoformat()
                }

                # Add OCR extracted data if provided (sanitized)
                if ocr_data:
                    updated_meta["ocr_extracted"] = self._sanitize_ocr_data(ocr_data)

                # Update database record
                db.execute(
                    text("""
                        UPDATE scriptclient.screenshot
                        SET meta = :meta, updated_at = NOW()
                        WHERE id = :id
                    """),
                    {
                        "id": screenshot_id,
                        "meta": updated_meta
                    }
                )

                db.commit()
                logger.info(f"Updated screenshot OCR results: {screenshot_id}")
                return True

        except Exception as e:
            logger.error(f"Error updating screenshot OCR results: {e}")
            return False

    def _sanitize_ocr_data(self, ocr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize OCR data to remove sensitive information before storage.

        Keeps only verification-relevant data, removes account numbers, etc.
        """
        sanitized = {}

        # Safe fields to keep
        safe_fields = [
            'amount', 'currency', 'bank', 'date', 'confidence',
            'verification_status', 'processing_time', 'timestamp'
        ]

        for field in safe_fields:
            if field in ocr_data:
                sanitized[field] = ocr_data[field]

        # Mask sensitive account information
        if 'account' in ocr_data and ocr_data['account']:
            account = str(ocr_data['account'])
            if len(account) > 4:
                sanitized['account_masked'] = '***' + account[-4:]
            else:
                sanitized['account_masked'] = '***'

        return sanitized

    async def get_screenshot_by_id(
        self,
        screenshot_id: str,
        tenant_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get screenshot metadata by database ID.

        Args:
            screenshot_id: Database screenshot ID
            tenant_id: Optional tenant ID for validation

        Returns:
            Screenshot metadata dict or None if not found
        """
        try:
            with get_db_session() as db:
                query = """
                    SELECT id, tenant_id, file_path, file_url, verified,
                           verified_at, verified_by, meta, created_at, updated_at
                    FROM scriptclient.screenshot
                    WHERE id = :id
                """

                params = {"id": screenshot_id}

                # Add tenant filter if provided for security
                if tenant_id:
                    query += " AND tenant_id = :tenant_id"
                    params["tenant_id"] = tenant_id

                result = db.execute(text(query), params).fetchone()

                if result:
                    return {
                        'id': str(result.id),
                        'tenant_id': str(result.tenant_id),
                        'gridfs_file_id': result.file_path,
                        'download_url': result.file_url,
                        'verified': result.verified,
                        'verified_at': result.verified_at.isoformat() if result.verified_at else None,
                        'verified_by': str(result.verified_by) if result.verified_by else None,
                        'metadata': result.meta or {},
                        'created_at': result.created_at.isoformat(),
                        'updated_at': result.updated_at.isoformat()
                    }
                return None

        except Exception as e:
            logger.error(f"Error getting screenshot by ID: {e}")
            return None

    async def get_screenshot_image_data(
        self,
        screenshot_id: str,
        tenant_id: str
    ) -> Optional[Tuple[bytes, str, str]]:
        """
        Get actual image data from GridFS for a screenshot.

        Args:
            screenshot_id: Database screenshot ID
            tenant_id: Tenant ID for security validation

        Returns:
            Tuple of (image_data, content_type, filename) or None if not found
        """
        try:
            # Get screenshot metadata first
            screenshot = await self.get_screenshot_by_id(screenshot_id, tenant_id)
            if not screenshot:
                logger.error(f"Screenshot not found or access denied: {screenshot_id}")
                return None

            # Get image from GridFS
            if self._is_storage_available():
                gridfs_file_id = screenshot['gridfs_file_id']
                result = await self._storage.get_file(gridfs_file_id, UUID(tenant_id))

                if result:
                    content, content_type, filename = result
                    logger.info(f"Retrieved screenshot from GridFS: {screenshot_id}")
                    return content, content_type, filename
                else:
                    logger.error(f"Image not found in GridFS: {gridfs_file_id}")
                    return None
            else:
                # Mock mode - return placeholder
                logger.warning("GridFS not available - returning mock image")
                return b"mock image data", "image/jpeg", "mock.jpg"

        except Exception as e:
            logger.error(f"Error retrieving screenshot image: {e}")
            return None

    async def mark_as_verified(
        self,
        screenshot_id: str,
        verified_by: str,
        verification_method: str = "manual_telegram"
    ) -> bool:
        """
        Mark screenshot as manually verified.

        Args:
            screenshot_id: Database screenshot ID
            verified_by: User ID who verified
            verification_method: How it was verified

        Returns:
            True if updated successfully
        """
        try:
            with get_db_session() as db:
                # Get current metadata
                current_result = db.execute(
                    text("SELECT meta FROM scriptclient.screenshot WHERE id = :id"),
                    {"id": screenshot_id}
                ).fetchone()

                if not current_result:
                    return False

                current_meta = current_result.meta or {}

                # Update metadata with verification info
                updated_meta = {
                    **current_meta,
                    "verification_method": verification_method,
                    "manually_verified": True,
                    "verification_timestamp": datetime.now(timezone.utc).isoformat()
                }

                # Update database record
                db.execute(
                    text("""
                        UPDATE scriptclient.screenshot
                        SET verified = true,
                            verified_at = NOW(),
                            verified_by = :verified_by,
                            meta = :meta,
                            updated_at = NOW()
                        WHERE id = :id
                    """),
                    {
                        "id": screenshot_id,
                        "verified_by": verified_by,
                        "meta": updated_meta
                    }
                )

                db.commit()
                logger.info(f"Marked screenshot as verified: {screenshot_id} by {verified_by}")
                return True

        except Exception as e:
            logger.error(f"Error marking screenshot as verified: {e}")
            return False

    async def get_screenshots_for_invoice(
        self,
        invoice_id: str,
        tenant_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all screenshots associated with an invoice.

        Args:
            invoice_id: Invoice ID
            tenant_id: Tenant ID for filtering

        Returns:
            List of screenshot metadata dictionaries
        """
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT id, file_path, file_url, verified, verified_at,
                               verified_by, meta, created_at
                        FROM scriptclient.screenshot
                        WHERE tenant_id = :tenant_id
                          AND meta->>'invoice_id' = :invoice_id
                        ORDER BY created_at DESC
                    """),
                    {
                        "tenant_id": tenant_id,
                        "invoice_id": invoice_id
                    }
                ).fetchall()

                screenshots = []
                for row in result:
                    screenshots.append({
                        'id': str(row.id),
                        'gridfs_file_id': row.file_path,
                        'download_url': row.file_url,
                        'verified': row.verified,
                        'verified_at': row.verified_at.isoformat() if row.verified_at else None,
                        'verified_by': str(row.verified_by) if row.verified_by else None,
                        'metadata': row.meta or {},
                        'created_at': row.created_at.isoformat()
                    })

                return screenshots

        except Exception as e:
            logger.error(f"Error getting screenshots for invoice: {e}")
            return []

    async def cleanup_old_screenshots(self, days_old: int = 30) -> int:
        """
        Clean up screenshots older than specified days.

        Args:
            days_old: Number of days after which to delete screenshots

        Returns:
            Number of screenshots deleted
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            deleted_count = 0

            with get_db_session() as db:
                # Get old screenshots
                old_screenshots = db.execute(
                    text("""
                        SELECT id, file_path, tenant_id
                        FROM scriptclient.screenshot
                        WHERE created_at < :cutoff_date
                        ORDER BY created_at ASC
                        LIMIT 100
                    """),
                    {"cutoff_date": cutoff_date}
                ).fetchall()

                for screenshot in old_screenshots:
                    try:
                        # Delete from GridFS
                        if self._is_storage_available():
                            await self._storage.delete_file(screenshot.file_path)

                        # Delete database record
                        db.execute(
                            text("DELETE FROM scriptclient.screenshot WHERE id = :id"),
                            {"id": screenshot.id}
                        )

                        deleted_count += 1
                        logger.info(f"Deleted old screenshot: {screenshot.id}")

                    except Exception as e:
                        logger.error(f"Error deleting screenshot {screenshot.id}: {e}")

                db.commit()

            logger.info(f"Cleanup completed: deleted {deleted_count} screenshots")
            return deleted_count

        except Exception as e:
            logger.error(f"Error during screenshot cleanup: {e}")
            return 0