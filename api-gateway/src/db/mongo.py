# api-gateway/src/db/mongo.py
"""MongoDB connections for API Gateway."""

from typing import Dict, Optional
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.config import settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manages connections to multiple MongoDB databases."""

    def __init__(self):
        self.clients: Dict[str, AsyncIOMotorClient] = {}
        self.databases: Dict[str, AsyncIOMotorDatabase] = {}

    async def connect(self):
        """Connect to all configured MongoDB databases."""
        connections = [
            ("invoice", settings.MONGO_URL_INVOICE, settings.MONGO_DB_INVOICE),
            ("scriptclient", settings.MONGO_URL_SCRIPTCLIENT, settings.MONGO_DB_SCRIPTCLIENT),
            ("audit_sales", settings.MONGO_URL_AUDIT_SALES, settings.MONGO_DB_AUDIT_SALES),
            ("ads_alert", settings.MONGO_URL_ADS_ALERT, settings.MONGO_DB_ADS_ALERT),
        ]

        for name, url, db_name in connections:
            if url:
                try:
                    client = AsyncIOMotorClient(url)
                    # Test connection
                    await client.admin.command("ping")
                    self.clients[name] = client
                    self.databases[name] = client[db_name]
                    logger.info(f"Connected to MongoDB: {name}")
                except Exception as e:
                    logger.warning(f"Failed to connect to MongoDB {name}: {e}")
            else:
                logger.info(f"MongoDB {name} not configured (URL not provided)")

    def get_db(self, name: str) -> Optional[AsyncIOMotorDatabase]:
        """Get a MongoDB database by name."""
        return self.databases.get(name)

    def is_connected(self, name: str) -> bool:
        """Check if a database is connected."""
        return name in self.databases

    async def close(self):
        """Close all MongoDB connections."""
        for name, client in self.clients.items():
            client.close()
            logger.info(f"Closed MongoDB connection: {name}")
        self.clients.clear()
        self.databases.clear()

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all MongoDB connections."""
        status = {}
        for name, client in self.clients.items():
            try:
                await client.admin.command("ping")
                status[name] = True
            except Exception:
                status[name] = False
        return status


# Global MongoDB manager instance
mongo_manager = MongoDBManager()
