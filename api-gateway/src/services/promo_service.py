# api-gateway/src/services/promo_service.py
"""Promotion/Ads Alert service for MongoDB operations."""

import logging
from typing import Dict, Any, List, Optional

from src.db import mongo_manager

logger = logging.getLogger(__name__)


class PromoService:
    """Service for interacting with Ads Alert MongoDB."""

    @property
    def db(self):
        """Get the ads_alert database."""
        return mongo_manager.get_db("ads_alert")

    async def get_stats(self) -> Dict[str, Any]:
        """Get promo service statistics."""
        if not self.db:
            return {"status": "not_connected"}

        try:
            chats = await self.db.chats.count_documents({})
            promos = await self.db.promotions.count_documents({})

            return {
                "status": "connected",
                "registered_chats": chats,
                "promotions": promos
            }
        except Exception as e:
            logger.error(f"Error getting promo stats: {e}")
            return {"status": "error", "message": str(e)}

    async def get_registered_chats(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of registered chats."""
        if not self.db:
            return []

        try:
            cursor = self.db.chats.find().limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting registered chats: {e}")
            return []

    async def get_current_status(self) -> Optional[Dict[str, Any]]:
        """Get current promotion status."""
        if not self.db:
            return None

        try:
            # Get the latest promotion status
            status = await self.db.status.find_one(sort=[("updatedAt", -1)])
            if status:
                return {
                    "active": status.get("active", False),
                    "last_sent": status.get("lastSent"),
                    "next_scheduled": status.get("nextScheduled")
                }
            return None
        except Exception as e:
            logger.error(f"Error getting promo status: {e}")
            return None

    async def get_promotions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of promotions."""
        if not self.db:
            return []

        try:
            cursor = self.db.promotions.find().sort("createdAt", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting promotions: {e}")
            return []


# Global service instance
promo_service = PromoService()
