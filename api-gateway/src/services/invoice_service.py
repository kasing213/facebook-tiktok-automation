# api-gateway/src/services/invoice_service.py
"""Invoice Generator service for MongoDB operations."""

import logging
from typing import Dict, Any, List, Optional

from src.db import mongo_manager

logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for interacting with Invoice Generator MongoDB."""

    @property
    def db(self):
        """Get the invoice database."""
        return mongo_manager.get_db("invoice")

    async def get_stats(self) -> Dict[str, Any]:
        """Get invoice service statistics."""
        if not self.db:
            return {"status": "not_connected"}

        try:
            customers = await self.db.customers.count_documents({})
            invoices = await self.db.invoices.count_documents({})

            return {
                "status": "connected",
                "customers": customers,
                "invoices": invoices
            }
        except Exception as e:
            logger.error(f"Error getting invoice stats: {e}")
            return {"status": "error", "message": str(e)}

    async def get_customers(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of customers."""
        if not self.db:
            return []

        try:
            cursor = self.db.customers.find().limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting customers: {e}")
            return []

    async def get_invoices(
        self,
        customer_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get list of invoices."""
        if not self.db:
            return []

        try:
            query = {"customerId": customer_id} if customer_id else {}
            cursor = self.db.invoices.find(query).sort("createdAt", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting invoices: {e}")
            return []

    async def search_customers(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search customers by name."""
        if not self.db:
            return []

        try:
            cursor = self.db.customers.find({
                "name": {"$regex": query, "$options": "i"}
            }).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error searching customers: {e}")
            return []


# Global service instance
invoice_service = InvoiceService()
