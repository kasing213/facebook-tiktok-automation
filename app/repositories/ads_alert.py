# app/repositories/ads_alert.py
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, or_
from app.core.models import (
    AdsAlertChat, AdsAlertPromotion, AdsAlertPromoStatus,
    AdsAlertMediaFolder, AdsAlertMedia, AdsAlertBroadcastLog,
    PromotionStatus, BroadcastStatus
)
from app.repositories.base import BaseRepository


class AdsAlertChatRepository(BaseRepository[AdsAlertChat]):
    """Repository for ads_alert chat operations"""

    def __init__(self, db: Session):
        super().__init__(db, AdsAlertChat)

    def get_by_tenant(
        self,
        tenant_id: UUID,
        subscribed_only: bool = False,
        active_only: bool = True,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[AdsAlertChat]:
        """Get all chats for a tenant"""
        query = self.db.query(AdsAlertChat).filter(AdsAlertChat.tenant_id == tenant_id)
        if active_only:
            query = query.filter(AdsAlertChat.is_active == True)
        if subscribed_only:
            query = query.filter(AdsAlertChat.subscribed == True)
        if tags:
            query = query.filter(AdsAlertChat.tags.overlap(tags))
        return query.order_by(desc(AdsAlertChat.created_at)).limit(limit).all()

    def get_by_chat_id(self, tenant_id: UUID, chat_id: str) -> Optional[AdsAlertChat]:
        """Get chat by telegram/platform chat_id"""
        return self.db.query(AdsAlertChat).filter(
            and_(
                AdsAlertChat.tenant_id == tenant_id,
                AdsAlertChat.chat_id == chat_id
            )
        ).first()

    def get_by_chat_id_global(self, chat_id: str) -> Optional[AdsAlertChat]:
        """Get chat by telegram/platform chat_id across all tenants"""
        return self.db.query(AdsAlertChat).filter(
            AdsAlertChat.chat_id == chat_id
        ).first()

    def get_by_id_and_tenant(self, id: UUID, tenant_id: UUID) -> Optional[AdsAlertChat]:
        """Get chat by ID ensuring tenant isolation"""
        return self.db.query(AdsAlertChat).filter(
            and_(
                AdsAlertChat.id == id,
                AdsAlertChat.tenant_id == tenant_id
            )
        ).first()

    def create_with_tenant(self, tenant_id: UUID, **kwargs) -> AdsAlertChat:
        """Create chat with tenant isolation"""
        kwargs['tenant_id'] = tenant_id
        return self.create(**kwargs)

    def update_by_tenant(self, id: UUID, tenant_id: UUID, **kwargs) -> Optional[AdsAlertChat]:
        """Update chat ensuring tenant isolation"""
        chat = self.get_by_id_and_tenant(id, tenant_id)
        if not chat:
            return None
        for key, value in kwargs.items():
            if hasattr(chat, key):
                setattr(chat, key, value)
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def soft_delete_by_tenant(self, id: UUID, tenant_id: UUID) -> bool:
        """Soft delete chat by setting is_active=False"""
        updated = self.db.query(AdsAlertChat).filter(
            and_(
                AdsAlertChat.id == id,
                AdsAlertChat.tenant_id == tenant_id
            )
        ).update({"is_active": False})
        self.db.commit()
        return updated > 0

    def count_by_tenant(self, tenant_id: UUID, subscribed_only: bool = False) -> int:
        """Count chats for a tenant"""
        query = self.db.query(AdsAlertChat).filter(
            and_(
                AdsAlertChat.tenant_id == tenant_id,
                AdsAlertChat.is_active == True
            )
        )
        if subscribed_only:
            query = query.filter(AdsAlertChat.subscribed == True)
        return query.count()

    # ==========================================
    # Customer-based targeting methods
    # ==========================================

    def get_by_customer_id(self, tenant_id: UUID, customer_id: UUID) -> Optional[AdsAlertChat]:
        """Get chat record by invoice customer ID"""
        return self.db.query(AdsAlertChat).filter(
            and_(
                AdsAlertChat.tenant_id == tenant_id,
                AdsAlertChat.customer_id == customer_id
            )
        ).first()

    def get_chats_by_customer_ids(
        self,
        tenant_id: UUID,
        customer_ids: List[UUID],
        subscribed_only: bool = True
    ) -> List[AdsAlertChat]:
        """Get chats for specific invoice customers"""
        query = self.db.query(AdsAlertChat).filter(
            and_(
                AdsAlertChat.tenant_id == tenant_id,
                AdsAlertChat.customer_id.in_(customer_ids),
                AdsAlertChat.is_active == True
            )
        )
        if subscribed_only:
            query = query.filter(AdsAlertChat.subscribed == True)
        return query.all()

    def get_all_customer_chats(
        self,
        tenant_id: UUID,
        subscribed_only: bool = True
    ) -> List[AdsAlertChat]:
        """Get all chats that are linked to invoice customers"""
        query = self.db.query(AdsAlertChat).filter(
            and_(
                AdsAlertChat.tenant_id == tenant_id,
                AdsAlertChat.customer_id.isnot(None),  # Must have customer link
                AdsAlertChat.is_active == True
            )
        )
        if subscribed_only:
            query = query.filter(AdsAlertChat.subscribed == True)
        return query.order_by(desc(AdsAlertChat.created_at)).all()

    def create_for_customer(
        self,
        tenant_id: UUID,
        customer_id: UUID,
        chat_id: str,
        customer_name: str,
        platform: str = "telegram"
    ) -> AdsAlertChat:
        """Create chat record linked to an invoice customer"""
        return self.create(
            tenant_id=tenant_id,
            customer_id=customer_id,
            platform=platform,
            chat_id=chat_id,
            chat_name=f"Customer: {customer_name}",
            customer_name=customer_name,
            subscribed=True,
            is_active=True
        )

    def update_subscription_by_chat_id(
        self,
        chat_id: str,
        subscribed: bool
    ) -> bool:
        """Update subscription status by telegram chat_id"""
        updated = self.db.query(AdsAlertChat).filter(
            AdsAlertChat.chat_id == chat_id
        ).update({"subscribed": subscribed})
        self.db.commit()
        return updated > 0

    def count_customer_chats(self, tenant_id: UUID, subscribed_only: bool = False) -> int:
        """Count chats linked to invoice customers"""
        query = self.db.query(AdsAlertChat).filter(
            and_(
                AdsAlertChat.tenant_id == tenant_id,
                AdsAlertChat.customer_id.isnot(None),
                AdsAlertChat.is_active == True
            )
        )
        if subscribed_only:
            query = query.filter(AdsAlertChat.subscribed == True)
        return query.count()


class AdsAlertPromotionRepository(BaseRepository[AdsAlertPromotion]):
    """Repository for ads_alert promotion operations"""

    def __init__(self, db: Session):
        super().__init__(db, AdsAlertPromotion)

    def get_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[PromotionStatus] = None,
        limit: int = 50
    ) -> List[AdsAlertPromotion]:
        """Get all promotions for a tenant"""
        query = self.db.query(AdsAlertPromotion).filter(
            AdsAlertPromotion.tenant_id == tenant_id
        )
        if status:
            query = query.filter(AdsAlertPromotion.status == status)
        return query.order_by(desc(AdsAlertPromotion.created_at)).limit(limit).all()

    def get_by_id_and_tenant(self, id: UUID, tenant_id: UUID) -> Optional[AdsAlertPromotion]:
        """Get promotion by ID ensuring tenant isolation"""
        return self.db.query(AdsAlertPromotion).filter(
            and_(
                AdsAlertPromotion.id == id,
                AdsAlertPromotion.tenant_id == tenant_id
            )
        ).first()

    def get_due_promotions(self) -> List[AdsAlertPromotion]:
        """Get all scheduled promotions that are due to be sent"""
        now = datetime.now(timezone.utc)
        return self.db.query(AdsAlertPromotion).filter(
            and_(
                AdsAlertPromotion.status == PromotionStatus.scheduled,
                AdsAlertPromotion.scheduled_at <= now
            )
        ).all()

    def create_with_tenant(self, tenant_id: UUID, created_by: Optional[UUID] = None, **kwargs) -> AdsAlertPromotion:
        """Create promotion with tenant isolation"""
        kwargs['tenant_id'] = tenant_id
        kwargs['created_by'] = created_by
        return self.create(**kwargs)

    def update_by_tenant(self, id: UUID, tenant_id: UUID, **kwargs) -> Optional[AdsAlertPromotion]:
        """Update promotion ensuring tenant isolation"""
        promotion = self.get_by_id_and_tenant(id, tenant_id)
        if not promotion:
            return None
        for key, value in kwargs.items():
            if hasattr(promotion, key):
                setattr(promotion, key, value)
        self.db.commit()
        self.db.refresh(promotion)
        return promotion

    def mark_as_sent(self, id: UUID, tenant_id: UUID) -> Optional[AdsAlertPromotion]:
        """Mark promotion as sent"""
        return self.update_by_tenant(
            id, tenant_id,
            status=PromotionStatus.sent,
            sent_at=datetime.now(timezone.utc)
        )

    def delete_by_tenant(self, id: UUID, tenant_id: UUID) -> bool:
        """Hard delete promotion"""
        deleted = self.db.query(AdsAlertPromotion).filter(
            and_(
                AdsAlertPromotion.id == id,
                AdsAlertPromotion.tenant_id == tenant_id
            )
        ).delete()
        self.db.commit()
        return deleted > 0

    def count_by_tenant(self, tenant_id: UUID, status: Optional[PromotionStatus] = None) -> int:
        """Count promotions for a tenant"""
        query = self.db.query(AdsAlertPromotion).filter(
            AdsAlertPromotion.tenant_id == tenant_id
        )
        if status:
            query = query.filter(AdsAlertPromotion.status == status)
        return query.count()


class AdsAlertMediaFolderRepository(BaseRepository[AdsAlertMediaFolder]):
    """Repository for ads_alert media folder operations"""

    def __init__(self, db: Session):
        super().__init__(db, AdsAlertMediaFolder)

    def get_by_tenant(
        self,
        tenant_id: UUID,
        parent_id: Optional[UUID] = None
    ) -> List[AdsAlertMediaFolder]:
        """Get folders for a tenant, optionally filtered by parent"""
        query = self.db.query(AdsAlertMediaFolder).filter(
            AdsAlertMediaFolder.tenant_id == tenant_id
        )
        if parent_id:
            query = query.filter(AdsAlertMediaFolder.parent_id == parent_id)
        else:
            query = query.filter(AdsAlertMediaFolder.parent_id.is_(None))
        return query.order_by(asc(AdsAlertMediaFolder.name)).all()

    def get_all_by_tenant(self, tenant_id: UUID) -> List[AdsAlertMediaFolder]:
        """Get all folders for a tenant (for tree view)"""
        return self.db.query(AdsAlertMediaFolder).filter(
            AdsAlertMediaFolder.tenant_id == tenant_id
        ).order_by(asc(AdsAlertMediaFolder.name)).all()

    def get_by_id_and_tenant(self, id: UUID, tenant_id: UUID) -> Optional[AdsAlertMediaFolder]:
        """Get folder by ID ensuring tenant isolation"""
        return self.db.query(AdsAlertMediaFolder).filter(
            and_(
                AdsAlertMediaFolder.id == id,
                AdsAlertMediaFolder.tenant_id == tenant_id
            )
        ).first()

    def create_with_tenant(
        self,
        tenant_id: UUID,
        name: str,
        parent_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None
    ) -> AdsAlertMediaFolder:
        """Create folder with tenant isolation"""
        return self.create(
            tenant_id=tenant_id,
            name=name,
            parent_id=parent_id,
            created_by=created_by
        )

    def delete_by_tenant(self, id: UUID, tenant_id: UUID) -> bool:
        """Delete folder (cascades to children and moves media to null folder)"""
        deleted = self.db.query(AdsAlertMediaFolder).filter(
            and_(
                AdsAlertMediaFolder.id == id,
                AdsAlertMediaFolder.tenant_id == tenant_id
            )
        ).delete()
        self.db.commit()
        return deleted > 0


class AdsAlertMediaRepository(BaseRepository[AdsAlertMedia]):
    """Repository for ads_alert media operations"""

    def __init__(self, db: Session):
        super().__init__(db, AdsAlertMedia)

    def get_by_tenant(
        self,
        tenant_id: UUID,
        folder_id: Optional[UUID] = None,
        file_type_prefix: Optional[str] = None,
        limit: int = 100
    ) -> List[AdsAlertMedia]:
        """Get media files for a tenant"""
        query = self.db.query(AdsAlertMedia).filter(
            AdsAlertMedia.tenant_id == tenant_id
        )
        if folder_id:
            query = query.filter(AdsAlertMedia.folder_id == folder_id)
        elif folder_id is None:
            # Root folder (no folder)
            query = query.filter(AdsAlertMedia.folder_id.is_(None))
        if file_type_prefix:
            query = query.filter(AdsAlertMedia.file_type.startswith(file_type_prefix))
        return query.order_by(desc(AdsAlertMedia.created_at)).limit(limit).all()

    def get_all_by_tenant(self, tenant_id: UUID, limit: int = 500) -> List[AdsAlertMedia]:
        """Get all media for a tenant regardless of folder"""
        return self.db.query(AdsAlertMedia).filter(
            AdsAlertMedia.tenant_id == tenant_id
        ).order_by(desc(AdsAlertMedia.created_at)).limit(limit).all()

    def get_by_id_and_tenant(self, id: UUID, tenant_id: UUID) -> Optional[AdsAlertMedia]:
        """Get media by ID ensuring tenant isolation"""
        return self.db.query(AdsAlertMedia).filter(
            and_(
                AdsAlertMedia.id == id,
                AdsAlertMedia.tenant_id == tenant_id
            )
        ).first()

    def get_by_ids_and_tenant(self, ids: List[UUID], tenant_id: UUID) -> List[AdsAlertMedia]:
        """Get multiple media files by IDs"""
        return self.db.query(AdsAlertMedia).filter(
            and_(
                AdsAlertMedia.id.in_(ids),
                AdsAlertMedia.tenant_id == tenant_id
            )
        ).all()

    def create_with_tenant(
        self,
        tenant_id: UUID,
        filename: str,
        storage_path: str,
        file_type: str,
        original_filename: Optional[str] = None,
        folder_id: Optional[UUID] = None,
        file_size: Optional[int] = None,
        thumbnail_path: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[int] = None,
        created_by: Optional[UUID] = None,
        meta: Optional[dict] = None
    ) -> AdsAlertMedia:
        """Create media record with tenant isolation"""
        return self.create(
            tenant_id=tenant_id,
            filename=filename,
            original_filename=original_filename,
            storage_path=storage_path,
            file_type=file_type,
            folder_id=folder_id,
            file_size=file_size,
            thumbnail_path=thumbnail_path,
            width=width,
            height=height,
            duration=duration,
            created_by=created_by,
            meta=meta
        )

    def delete_by_tenant(self, id: UUID, tenant_id: UUID) -> Optional[AdsAlertMedia]:
        """Delete media and return the record (for storage cleanup)"""
        media = self.get_by_id_and_tenant(id, tenant_id)
        if media:
            self.db.delete(media)
            self.db.commit()
        return media

    def search_by_filename(
        self,
        tenant_id: UUID,
        search_term: str,
        limit: int = 50
    ) -> List[AdsAlertMedia]:
        """Search media by filename"""
        search_pattern = f"%{search_term}%"
        return self.db.query(AdsAlertMedia).filter(
            and_(
                AdsAlertMedia.tenant_id == tenant_id,
                or_(
                    AdsAlertMedia.filename.ilike(search_pattern),
                    AdsAlertMedia.original_filename.ilike(search_pattern)
                )
            )
        ).order_by(desc(AdsAlertMedia.created_at)).limit(limit).all()


class AdsAlertBroadcastLogRepository(BaseRepository[AdsAlertBroadcastLog]):
    """Repository for ads_alert broadcast log operations"""

    def __init__(self, db: Session):
        super().__init__(db, AdsAlertBroadcastLog)

    def get_by_promotion(
        self,
        promotion_id: UUID,
        tenant_id: UUID
    ) -> List[AdsAlertBroadcastLog]:
        """Get all broadcast logs for a promotion"""
        return self.db.query(AdsAlertBroadcastLog).filter(
            and_(
                AdsAlertBroadcastLog.promotion_id == promotion_id,
                AdsAlertBroadcastLog.tenant_id == tenant_id
            )
        ).all()

    def create_log(
        self,
        tenant_id: UUID,
        promotion_id: UUID,
        chat_id: UUID,
        status: BroadcastStatus = BroadcastStatus.pending
    ) -> AdsAlertBroadcastLog:
        """Create a broadcast log entry"""
        return self.create(
            tenant_id=tenant_id,
            promotion_id=promotion_id,
            chat_id=chat_id,
            status=status
        )

    def mark_as_sent(self, id: UUID) -> Optional[AdsAlertBroadcastLog]:
        """Mark broadcast as sent"""
        log = self.get_by_id(id)
        if log:
            log.status = BroadcastStatus.sent
            log.sent_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(log)
        return log

    def mark_as_failed(self, id: UUID, error_message: str) -> Optional[AdsAlertBroadcastLog]:
        """Mark broadcast as failed"""
        log = self.get_by_id(id)
        if log:
            log.status = BroadcastStatus.failed
            log.error_message = error_message
            self.db.commit()
            self.db.refresh(log)
        return log

    def get_stats_by_promotion(self, promotion_id: UUID, tenant_id: UUID) -> dict:
        """Get broadcast statistics for a promotion"""
        logs = self.get_by_promotion(promotion_id, tenant_id)
        return {
            "total": len(logs),
            "sent": sum(1 for l in logs if l.status == BroadcastStatus.sent),
            "failed": sum(1 for l in logs if l.status == BroadcastStatus.failed),
            "pending": sum(1 for l in logs if l.status == BroadcastStatus.pending)
        }
