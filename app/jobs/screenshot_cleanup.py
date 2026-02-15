"""
Screenshot Cleanup Job - Automatic cleanup of old payment screenshots.

This job runs daily to clean up screenshots older than 30 days from both
MongoDB GridFS storage and the PostgreSQL screenshot table to prevent
storage bloat while maintaining audit trail for recent transactions.
"""

import logging
import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import get_db_session_with_retry

logger = logging.getLogger(__name__)


class ScreenshotCleanupJob:
    """Job for cleaning up old screenshots to manage storage usage."""

    def __init__(self, retention_days: int = 30):
        """
        Initialize cleanup job.

        Args:
            retention_days: Number of days to retain screenshots (default: 30)
        """
        self.retention_days = retention_days
        self.stats = {
            "total_processed": 0,
            "screenshots_deleted": 0,
            "storage_freed_mb": 0.0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }

    async def run_cleanup(self) -> Dict[str, Any]:
        """
        Run screenshot cleanup job.

        Returns:
            Dict with cleanup statistics
        """
        self.stats["start_time"] = datetime.now(timezone.utc)
        logger.info(f"🧹 Starting screenshot cleanup job (retention: {self.retention_days} days)")

        try:
            # Import here to avoid circular dependencies
            from api_gateway.src.services.payment_screenshot_service import PaymentScreenshotService
            screenshot_service = PaymentScreenshotService()

            # Run cleanup
            deleted_count = await screenshot_service.cleanup_old_screenshots(self.retention_days)

            self.stats["screenshots_deleted"] = deleted_count
            self.stats["total_processed"] = deleted_count
            self.stats["end_time"] = datetime.now(timezone.utc)

            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

            logger.info(
                f"✅ Screenshot cleanup completed successfully in {duration:.1f}s: "
                f"{deleted_count} screenshots deleted"
            )

            return {
                "success": True,
                "deleted_count": deleted_count,
                "duration_seconds": duration,
                "retention_days": self.retention_days,
                "completion_time": self.stats["end_time"].isoformat()
            }

        except Exception as e:
            self.stats["errors"] += 1
            self.stats["end_time"] = datetime.now(timezone.utc)

            logger.error(f"❌ Screenshot cleanup job failed: {e}", exc_info=True)

            return {
                "success": False,
                "error": str(e),
                "deleted_count": 0,
                "retention_days": self.retention_days,
                "completion_time": self.stats["end_time"].isoformat() if self.stats["end_time"] else None
            }

    async def get_cleanup_preview(self) -> Dict[str, Any]:
        """
        Get preview of what would be cleaned up without actually deleting.

        Returns:
            Dict with preview statistics
        """
        try:
            with get_db_session_with_retry() as db:
                from datetime import timedelta
                from sqlalchemy import text

                cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)

                # Get statistics of screenshots to be deleted
                result = db.execute(
                    text("""
                        SELECT
                            COUNT(*) as total_count,
                            COUNT(DISTINCT tenant_id) as tenant_count,
                            SUM(CASE
                                WHEN meta->>'file_size' IS NOT NULL
                                THEN (meta->>'file_size')::bigint
                                ELSE 0
                            END) as total_size_bytes,
                            MIN(created_at) as oldest_screenshot,
                            MAX(created_at) as newest_old_screenshot
                        FROM scriptclient.screenshot
                        WHERE created_at < :cutoff_date
                    """),
                    {"cutoff_date": cutoff_date}
                ).fetchone()

                if result.total_count == 0:
                    return {
                        "screenshots_to_delete": 0,
                        "tenants_affected": 0,
                        "storage_to_free_mb": 0.0,
                        "oldest_screenshot": None,
                        "cutoff_date": cutoff_date.isoformat(),
                        "message": "No screenshots older than retention period found"
                    }

                storage_mb = (result.total_size_bytes or 0) / (1024 * 1024)

                return {
                    "screenshots_to_delete": result.total_count,
                    "tenants_affected": result.tenant_count,
                    "storage_to_free_mb": round(storage_mb, 2),
                    "oldest_screenshot": result.oldest_screenshot.isoformat() if result.oldest_screenshot else None,
                    "newest_old_screenshot": result.newest_old_screenshot.isoformat() if result.newest_old_screenshot else None,
                    "cutoff_date": cutoff_date.isoformat(),
                    "retention_days": self.retention_days
                }

        except Exception as e:
            logger.error(f"Error getting cleanup preview: {e}")
            return {
                "error": str(e),
                "screenshots_to_delete": 0,
                "storage_to_free_mb": 0.0
            }

    def get_job_stats(self) -> Dict[str, Any]:
        """Get job execution statistics."""
        return self.stats.copy()


async def run_daily_cleanup():
    """Run daily screenshot cleanup (main entry point for scheduler)."""
    cleanup_job = ScreenshotCleanupJob(retention_days=30)
    result = await cleanup_job.run_cleanup()

    # Log audit trail for cleanup operation
    if result["success"]:
        try:
            with get_db_session_with_retry() as db:
                from app.services.ocr_audit_service import OCRAuditService
                from sqlalchemy import text

                # Log system cleanup action
                db.execute(
                    text("""
                        INSERT INTO audit_sales.ocr_verification_log (
                            tenant_id, action, new_status, verification_method,
                            verified_by_name, notes, created_at
                        ) VALUES (
                            '00000000-0000-0000-0000-000000000000',
                            'system_cleanup',
                            'completed',
                            'screenshot_cleanup_job',
                            'system',
                            :notes,
                            NOW()
                        )
                    """),
                    {
                        "notes": f"Daily screenshot cleanup: {result['deleted_count']} screenshots deleted, retention: {result['retention_days']} days"
                    }
                )
                db.commit()

        except Exception as e:
            logger.error(f"Failed to log cleanup audit: {e}")

    return result


async def preview_cleanup(retention_days: int = 30):
    """Preview what would be cleaned up (for manual inspection)."""
    cleanup_job = ScreenshotCleanupJob(retention_days=retention_days)
    preview = await cleanup_job.get_cleanup_preview()

    print("🔍 Screenshot Cleanup Preview")
    print(f"   Retention Period: {retention_days} days")
    print(f"   Cutoff Date: {preview.get('cutoff_date', 'N/A')}")
    print(f"   Screenshots to delete: {preview.get('screenshots_to_delete', 0)}")
    print(f"   Tenants affected: {preview.get('tenants_affected', 0)}")
    print(f"   Storage to free: {preview.get('storage_to_free_mb', 0)} MB")

    if preview.get('oldest_screenshot'):
        print(f"   Oldest screenshot: {preview['oldest_screenshot']}")

    if preview.get('error'):
        print(f"   ❌ Error: {preview['error']}")

    return preview


if __name__ == "__main__":
    """Run cleanup job directly for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Screenshot cleanup job")
    parser.add_argument("--preview", action="store_true", help="Preview cleanup without deleting")
    parser.add_argument("--retention-days", type=int, default=30, help="Retention period in days")
    parser.add_argument("--run", action="store_true", help="Run actual cleanup")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if args.preview:
        asyncio.run(preview_cleanup(args.retention_days))
    elif args.run:
        asyncio.run(run_daily_cleanup())
    else:
        print("Use --preview to see what would be deleted, or --run to execute cleanup")
        print("Example: python screenshot_cleanup.py --preview")
        print("         python screenshot_cleanup.py --run")