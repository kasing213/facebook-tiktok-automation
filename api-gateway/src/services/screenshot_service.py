# api-gateway/src/services/screenshot_service.py
"""Screenshot/Scriptclient service for MongoDB operations."""

import logging
from typing import Dict, Any, List

from src.db import mongo_manager

logger = logging.getLogger(__name__)


class ScreenshotService:
    """Service for interacting with Scriptclient MongoDB."""

    @property
    def db(self):
        """Get the scriptclient database."""
        return mongo_manager.get_db("scriptclient")

    async def get_stats(self) -> Dict[str, Any]:
        """Get screenshot service statistics."""
        if not self.db:
            return {"status": "not_connected"}

        try:
            total = await self.db.screenshots.count_documents({})
            verified = await self.db.screenshots.count_documents({"verified": True})
            pending = await self.db.screenshots.count_documents({"verified": False})

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
        if not self.db:
            return []

        try:
            cursor = self.db.screenshots.find({"verified": True}).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting verified screenshots: {e}")
            return []

    async def get_pending_screenshots(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of pending (unverified) screenshots."""
        if not self.db:
            return []

        try:
            cursor = self.db.screenshots.find({"verified": False}).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting pending screenshots: {e}")
            return []


# Global service instance
screenshot_service = ScreenshotService()
