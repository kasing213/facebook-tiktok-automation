# api-gateway/src/services/sales_service.py
"""Sales/Audit Sales service for MongoDB operations."""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.db import mongo_manager

logger = logging.getLogger(__name__)


class SalesService:
    """Service for interacting with Audit Sales MongoDB."""

    @property
    def db(self):
        """Get the audit_sales database."""
        return mongo_manager.get_db("audit_sales")

    async def get_stats(self) -> Dict[str, Any]:
        """Get sales service statistics."""
        if not self.db:
            return {"status": "not_connected"}

        try:
            total_records = await self.db.sales.count_documents({})

            # Get this month's count
            now = datetime.now()
            start_of_month = datetime(now.year, now.month, 1)
            this_month = await self.db.sales.count_documents({
                "date": {"$gte": start_of_month}
            })

            return {
                "status": "connected",
                "total_records": total_records,
                "this_month": this_month
            }
        except Exception as e:
            logger.error(f"Error getting sales stats: {e}")
            return {"status": "error", "message": str(e)}

    async def get_daily_summary(self, date: str) -> Optional[Dict[str, Any]]:
        """Get daily sales summary."""
        if not self.db:
            return None

        try:
            # Parse date
            target_date = datetime.strptime(date, "%Y-%m-%d")
            next_date = datetime(target_date.year, target_date.month, target_date.day + 1)

            # Aggregate sales for the day
            pipeline = [
                {
                    "$match": {
                        "date": {"$gte": target_date, "$lt": next_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$amount"},
                        "count": {"$sum": 1},
                        "average": {"$avg": "$amount"}
                    }
                }
            ]

            cursor = self.db.sales.aggregate(pipeline)
            results = await cursor.to_list(length=1)

            if results:
                return results[0]
            return {"total": 0, "count": 0, "average": 0}

        except Exception as e:
            logger.error(f"Error getting daily summary: {e}")
            return None

    async def get_sales(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of sales records."""
        if not self.db:
            return []

        try:
            cursor = self.db.sales.find().sort("date", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting sales: {e}")
            return []


# Global service instance
sales_service = SalesService()
