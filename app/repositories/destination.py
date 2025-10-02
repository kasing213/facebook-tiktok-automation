# app/repositories/destination.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.models import Destination, DestinationType
from .base import BaseRepository


class DestinationRepository(BaseRepository[Destination]):
    """Repository for destination operations"""

    def __init__(self, db: Session):
        super().__init__(db, Destination)

    def get_by_type(self, tenant_id: UUID, destination_type: DestinationType) -> List[Destination]:
        """Get all destinations of a specific type for a tenant"""
        return self.find_by(tenant_id=tenant_id, type=destination_type)

    def get_active_destinations(self, tenant_id: UUID) -> List[Destination]:
        """Get all active destinations for a tenant"""
        return self.find_by(tenant_id=tenant_id, is_active=True)

    def get_telegram_destination(self, tenant_id: UUID, chat_id: str) -> Optional[Destination]:
        """Get Telegram destination by chat ID"""
        destinations = self.get_by_type(tenant_id, DestinationType.telegram_chat)
        for dest in destinations:
            if dest.config.get("chat_id") == chat_id:
                return dest
        return None

    def create_telegram_destination(
        self,
        tenant_id: UUID,
        name: str,
        chat_id: str,
        chat_title: str = None
    ) -> Destination:
        """Create a new Telegram destination"""
        config = {
            "chat_id": chat_id,
            "chat_title": chat_title,
            "chat_type": "private"  # Can be extended to support groups/channels
        }

        return self.create(
            tenant_id=tenant_id,
            name=name,
            type=DestinationType.telegram_chat,
            config=config,
            is_active=True
        )

    def create_webhook_destination(
        self,
        tenant_id: UUID,
        name: str,
        webhook_url: str,
        headers: dict = None,
        auth_config: dict = None
    ) -> Destination:
        """Create a new webhook destination"""
        config = {
            "webhook_url": webhook_url,
            "headers": headers or {},
            "auth_config": auth_config or {},
            "timeout": 30
        }

        return self.create(
            tenant_id=tenant_id,
            name=name,
            type=DestinationType.webhook,
            config=config,
            is_active=True
        )

    def deactivate_destination(self, destination_id: UUID) -> Optional[Destination]:
        """Deactivate a destination"""
        return self.update(destination_id, is_active=False)