# api-gateway/src/services/promo_service.py
"""Promotion/Ads Alert service for PostgreSQL operations."""

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy import text

from src.db.postgres import get_db_session

logger = logging.getLogger(__name__)


class PromoService:
    """Service for interacting with Ads Alert schema in PostgreSQL."""

    async def get_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get promo service statistics for a specific tenant."""
        try:
            with get_db_session() as db:
                chats = db.execute(
                    text("SELECT COUNT(*) FROM ads_alert.chat WHERE tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id}
                ).scalar() or 0

                promos = db.execute(
                    text("SELECT COUNT(*) FROM ads_alert.promotion WHERE tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id}
                ).scalar() or 0

                return {
                    "status": "connected",
                    "registered_chats": chats,
                    "promotions": promos
                }
        except Exception as e:
            logger.error(f"Error getting promo stats: {e}")
            return {"status": "error", "message": str(e)}

    async def get_registered_chats(self, tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of registered chats for a specific tenant."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT id, tenant_id, platform, chat_id, chat_name, is_active, meta, created_at, updated_at
                        FROM ads_alert.chat
                        WHERE tenant_id = :tenant_id
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {"tenant_id": tenant_id, "limit": limit}
                )
                rows = result.fetchall()
                return [
                    {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "platform": row.platform,
                        "chat_id": row.chat_id,
                        "chat_name": row.chat_name,
                        "is_active": row.is_active,
                        "meta": row.meta or {},
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting registered chats: {e}")
            return []

    async def get_current_status(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get current promotion status for a specific tenant."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT id, tenant_id, active, last_sent, next_scheduled, meta, updated_at
                        FROM ads_alert.promo_status
                        WHERE tenant_id = :tenant_id
                        ORDER BY updated_at DESC
                        LIMIT 1
                    """),
                    {"tenant_id": tenant_id}
                )
                row = result.fetchone()
                if row:
                    return {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "active": row.active,
                        "last_sent": row.last_sent.isoformat() if row.last_sent else None,
                        "next_scheduled": row.next_scheduled.isoformat() if row.next_scheduled else None,
                        "meta": row.meta or {},
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting promo status: {e}")
            return None

    async def get_promotions(self, tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of promotions for a specific tenant."""
        try:
            with get_db_session() as db:
                result = db.execute(
                    text("""
                        SELECT id, tenant_id, title, content, status, sent_at, meta, created_at, updated_at
                        FROM ads_alert.promotion
                        WHERE tenant_id = :tenant_id
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {"tenant_id": tenant_id, "limit": limit}
                )
                rows = result.fetchall()
                return [
                    {
                        "id": str(row.id),
                        "tenant_id": str(row.tenant_id),
                        "title": row.title,
                        "content": row.content,
                        "status": row.status,
                        "sent_at": row.sent_at.isoformat() if row.sent_at else None,
                        "meta": row.meta or {},
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting promotions: {e}")
            return []


# Global service instance
promo_service = PromoService()
