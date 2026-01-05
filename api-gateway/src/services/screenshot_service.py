# api-gateway/src/services/screenshot_service.py
"""Screenshot/Scriptclient service for PostgreSQL operations."""

import logging
from typing import Dict, Any, List

from sqlalchemy import text

from src.db.postgres import get_db_session

logger = logging.getLogger(__name__)


class ScreenshotService:
    """Service for interacting with Scriptclient schema in PostgreSQL."""

    async def get_stats(self) -> Dict[str, Any]:
        """Get screenshot service statistics."""
        try:
            with get_db_session() as db:
                total = db.execute(
                    text("SELECT COUNT(*) FROM scriptclient.screenshot")
                ).scalar() or 0

                verified = db.execute(
                    text("SELECT COUNT(*) FROM scriptclient.screenshot WHERE verified = true")
                ).scalar() or 0

                pending = db.execute(
                    text("SELECT COUNT(*) FROM scriptclient.screenshot WHERE verified = false")
                ).scalar() or 0

                return {
                    "status": "connected",
                    "total": total,
                    "verified": verified,
                    "pending": pending
                }
        except Exception as e:
            logger.error(f"Error getting screenshot stats: {e}")
            return {"status": "error", "message": str(e)}

    async def get_verified_screenshots(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of verified screenshots."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT id, tenant_id, file_path, file_url, verified, verified_at, verified_by, meta, created_at, updated_at
                        FROM scriptclient.screenshot
                        WHERE verified = true
                        ORDER BY verified_at DESC
                        LIMIT :limit
                    """),
                    {"limit": limit}
                )
                rows = result.fetchall()
                return [
                    {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "file_path": row.file_path,
                        "file_url": row.file_url,
                        "verified": row.verified,
                        "verified_at": row.verified_at.isoformat() if row.verified_at else None,
                        "verified_by": str(row.verified_by) if row.verified_by else None,
                        "meta": row.meta or {},
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting verified screenshots: {e}")
            return []

    async def get_pending_screenshots(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of pending (unverified) screenshots."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT id, tenant_id, file_path, file_url, verified, verified_at, verified_by, meta, created_at, updated_at
                        FROM scriptclient.screenshot
                        WHERE verified = false
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {"limit": limit}
                )
                rows = result.fetchall()
                return [
                    {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "file_path": row.file_path,
                        "file_url": row.file_url,
                        "verified": row.verified,
                        "verified_at": row.verified_at.isoformat() if row.verified_at else None,
                        "verified_by": str(row.verified_by) if row.verified_by else None,
                        "meta": row.meta or {},
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting pending screenshots: {e}")
            return []


# Global service instance
screenshot_service = ScreenshotService()
