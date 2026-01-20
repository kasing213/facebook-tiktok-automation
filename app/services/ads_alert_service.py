# app/services/ads_alert_service.py
"""
Ads Alert Service - Business logic for promotional messaging system.
Handles media uploads to MongoDB GridFS and broadcasting to Telegram.
"""
import uuid
import logging
import httpx
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

try:
    import motor.motor_asyncio
    from bson import ObjectId
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False

from app.core.config import get_settings
from app.core.models import (
    AdsAlertChat, AdsAlertPromotion, AdsAlertMedia, AdsAlertMediaFolder,
    AdsAlertBroadcastLog, PromotionStatus, BroadcastStatus, PromotionTargetType,
    PromotionCustomerTargetType
)
from app.repositories.ads_alert import (
    AdsAlertChatRepository, AdsAlertPromotionRepository,
    AdsAlertMediaRepository, AdsAlertMediaFolderRepository,
    AdsAlertBroadcastLogRepository
)

logger = logging.getLogger(__name__)
settings = get_settings()


class GridFSStorageService:
    """Handle media uploads to MongoDB GridFS"""

    def __init__(self):
        self.mongo_url = settings.MONGO_URL_ADS_ALERT
        self._client = None
        self._db = None
        self._bucket = None

    def _is_configured(self) -> bool:
        """Check if MongoDB is properly configured"""
        return bool(self.mongo_url)

    async def _get_bucket(self) -> "AsyncIOMotorGridFSBucket":
        """Get or create GridFS bucket"""
        if not MOTOR_AVAILABLE:
            raise ImportError("motor is required for GridFS storage. Install with: pip install motor")

        if self._bucket is None:
            if not self._is_configured():
                raise ValueError("MongoDB not configured. Set MONGO_URL_ADS_ALERT in .env")

            self._client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_url)
            self._db = self._client.ads_alert
            self._bucket = AsyncIOMotorGridFSBucket(self._db)
        return self._bucket

    def get_public_url(self, file_id: str) -> str:
        """Get API URL for a file in GridFS"""
        return f"/api/ads-alert/media/file/{file_id}"

    async def upload_file(
        self,
        tenant_id: UUID,
        file_content: bytes,
        filename: str,
        content_type: str
    ) -> Tuple[str, str]:
        """
        Upload file to MongoDB GridFS.

        Returns:
            Tuple of (gridfs_file_id, download_url)
        """
        if not self._is_configured():
            # Fallback for development - return mock ID
            logger.warning("MongoDB not configured, using mock storage")
            mock_id = str(uuid.uuid4())
            return mock_id, f"/api/ads-alert/media/file/{mock_id}"

        try:
            bucket = await self._get_bucket()

            # Store with metadata for tenant isolation
            file_id = await bucket.upload_from_stream(
                filename,
                file_content,
                metadata={
                    "tenant_id": str(tenant_id),
                    "content_type": content_type,
                    "original_filename": filename,
                    "upload_timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

            gridfs_file_id = str(file_id)
            download_url = self.get_public_url(gridfs_file_id)

            logger.info(f"Uploaded media to GridFS: {gridfs_file_id}")
            return gridfs_file_id, download_url

        except Exception as e:
            logger.error(f"Error uploading to GridFS: {e}")
            raise

    async def delete_file(self, file_id: str) -> bool:
        """Delete file from GridFS"""
        if not self._is_configured():
            logger.warning("MongoDB not configured, skipping delete")
            return True

        try:
            bucket = await self._get_bucket()
            await bucket.delete(ObjectId(file_id))
            logger.info(f"Deleted media from GridFS: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting from GridFS: {e}")
            return False

    async def get_file(self, file_id: str, tenant_id: Optional[UUID] = None) -> Optional[Tuple[bytes, str, str]]:
        """
        Get file from GridFS with optional tenant validation.

        Returns:
            Tuple of (content, content_type, filename) or None if not found
        """
        if not self._is_configured():
            return None

        try:
            bucket = await self._get_bucket()

            # Find file by ID
            grid_out = await bucket.open_download_stream(ObjectId(file_id))

            # Validate tenant ownership if tenant_id provided
            metadata = grid_out.metadata or {}
            if tenant_id and metadata.get("tenant_id") != str(tenant_id):
                logger.warning(f"Tenant mismatch for file {file_id}")
                return None

            content = await grid_out.read()
            content_type = metadata.get("content_type", "application/octet-stream")
            filename = grid_out.filename

            return content, content_type, filename

        except Exception as e:
            logger.error(f"Error getting file from GridFS: {e}")
            return None


class BroadcastService:
    """Handle broadcasting promotions to Telegram chats via API Gateway"""

    def __init__(self):
        self.api_gateway_url = settings.API_GATEWAY_URL

    async def send_promotion_to_chat(
        self,
        chat_id: str,
        content: str,
        media_type: str,
        media_urls: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Send a promotion to a single chat via API Gateway.

        Returns:
            Tuple of (success, error_message)
        """
        if not self.api_gateway_url:
            logger.warning("API Gateway URL not configured")
            return False, "API Gateway not configured"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_gateway_url}/internal/telegram/broadcast",
                    json={
                        "chat_ids": [chat_id],
                        "content": content,
                        "media_type": media_type,
                        "media_urls": media_urls
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("results") and len(result["results"]) > 0:
                        first_result = result["results"][0]
                        if first_result.get("success"):
                            return True, None
                        else:
                            return False, first_result.get("error", "Unknown error")
                    return False, "No results returned"

                return False, f"HTTP {response.status_code}: {response.text}"

        except Exception as e:
            logger.error(f"Error broadcasting to chat {chat_id}: {e}")
            return False, str(e)

    async def broadcast_promotion(
        self,
        promotion: AdsAlertPromotion,
        chats: List[AdsAlertChat],
        db: Session
    ) -> dict:
        """
        Broadcast a promotion to multiple chats.

        Returns:
            dict with broadcast statistics
        """
        broadcast_log_repo = AdsAlertBroadcastLogRepository(db)
        results = {
            "total": len(chats),
            "sent": 0,
            "failed": 0,
            "results": []
        }

        for chat in chats:
            # Create broadcast log entry
            log = broadcast_log_repo.create_log(
                tenant_id=promotion.tenant_id,
                promotion_id=promotion.id,
                chat_id=chat.id,
                status=BroadcastStatus.pending
            )

            # Send to chat
            success, error = await self.send_promotion_to_chat(
                chat_id=chat.chat_id,
                content=promotion.content or "",
                media_type=promotion.media_type.value if promotion.media_type else "text",
                media_urls=promotion.media_urls or []
            )

            if success:
                broadcast_log_repo.mark_as_sent(log.id)
                results["sent"] += 1
                results["results"].append({
                    "chat_id": chat.chat_id,
                    "success": True
                })
            else:
                broadcast_log_repo.mark_as_failed(log.id, error or "Unknown error")
                results["failed"] += 1
                results["results"].append({
                    "chat_id": chat.chat_id,
                    "success": False,
                    "error": error
                })

        return results


class AdsAlertService:
    """Main service for Ads Alert operations"""

    def __init__(self, db: Session):
        self.db = db
        self.chat_repo = AdsAlertChatRepository(db)
        self.promotion_repo = AdsAlertPromotionRepository(db)
        self.media_repo = AdsAlertMediaRepository(db)
        self.folder_repo = AdsAlertMediaFolderRepository(db)
        self.broadcast_log_repo = AdsAlertBroadcastLogRepository(db)
        self.storage_service = GridFSStorageService()
        self.broadcast_service = BroadcastService()

    # ==================== Media Operations ====================

    async def upload_media(
        self,
        tenant_id: UUID,
        file_content: bytes,
        filename: str,
        content_type: str,
        folder_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None
    ) -> AdsAlertMedia:
        """Upload a media file and create database record"""
        # Upload to MongoDB GridFS
        gridfs_file_id, public_url = await self.storage_service.upload_file(
            tenant_id=tenant_id,
            file_content=file_content,
            filename=filename,
            content_type=content_type
        )

        # Create database record
        media = self.media_repo.create_with_tenant(
            tenant_id=tenant_id,
            filename=filename,
            original_filename=filename,
            storage_path=gridfs_file_id,  # Store GridFS file ID as storage_path
            file_type=content_type,
            file_size=len(file_content),
            folder_id=folder_id,
            created_by=created_by
        )

        return media

    async def delete_media(self, media_id: UUID, tenant_id: UUID) -> bool:
        """Delete media file from storage and database"""
        media = self.media_repo.get_by_id_and_tenant(media_id, tenant_id)
        if not media:
            return False

        # Delete from MongoDB GridFS
        await self.storage_service.delete_file(media.storage_path)

        # Delete database record
        self.media_repo.delete_by_tenant(media_id, tenant_id)
        return True

    def get_media_url(self, file_id: str) -> str:
        """Get public URL for a media file"""
        return self.storage_service.get_public_url(file_id)

    # ==================== Promotion Operations ====================

    async def send_promotion_now(
        self,
        promotion_id: UUID,
        tenant_id: UUID
    ) -> dict:
        """Send a promotion immediately to all target chats"""
        promotion = self.promotion_repo.get_by_id_and_tenant(promotion_id, tenant_id)
        if not promotion:
            raise ValueError("Promotion not found")

        if promotion.status == PromotionStatus.sent:
            raise ValueError("Promotion has already been sent")

        # Build target chats list
        chats = []

        # Check for customer-based targeting first (takes priority if set)
        if hasattr(promotion, 'target_customer_type') and promotion.target_customer_type:
            if promotion.target_customer_type == PromotionCustomerTargetType.all_customers:
                # Target all invoice customers with linked Telegram
                chats = self.chat_repo.get_all_customer_chats(
                    tenant_id,
                    subscribed_only=True
                )
            elif promotion.target_customer_type == PromotionCustomerTargetType.selected_customers:
                # Target specific customers
                if promotion.target_customer_ids:
                    chats = self.chat_repo.get_chats_by_customer_ids(
                        tenant_id,
                        promotion.target_customer_ids,
                        subscribed_only=True
                    )

        # Fallback to existing chat-based targeting if no customer targeting or no chats found
        if not chats:
            if promotion.target_type == PromotionTargetType.selected and promotion.target_chat_ids:
                chats = [
                    self.chat_repo.get_by_id_and_tenant(chat_id, tenant_id)
                    for chat_id in promotion.target_chat_ids
                ]
                chats = [c for c in chats if c and c.subscribed and c.is_active]
            else:
                # Target all chats (including customer chats)
                chats = self.chat_repo.get_by_tenant(
                    tenant_id,
                    subscribed_only=True,
                    active_only=True
                )

        if not chats:
            raise ValueError("No target chats available")

        # Broadcast
        results = await self.broadcast_service.broadcast_promotion(
            promotion=promotion,
            chats=chats,
            db=self.db
        )

        # Mark promotion as sent
        self.promotion_repo.mark_as_sent(promotion_id, tenant_id)

        return {
            "promotion_id": promotion_id,
            **results
        }

    def schedule_promotion(
        self,
        promotion_id: UUID,
        tenant_id: UUID,
        scheduled_at: datetime
    ) -> AdsAlertPromotion:
        """Schedule a promotion for later sending"""
        promotion = self.promotion_repo.get_by_id_and_tenant(promotion_id, tenant_id)
        if not promotion:
            raise ValueError("Promotion not found")

        if promotion.status == PromotionStatus.sent:
            raise ValueError("Promotion has already been sent")

        if scheduled_at <= datetime.now(timezone.utc):
            raise ValueError("Scheduled time must be in the future")

        return self.promotion_repo.update_by_tenant(
            promotion_id,
            tenant_id,
            status=PromotionStatus.scheduled,
            scheduled_at=scheduled_at
        )

    # ==================== Stats ====================

    def get_stats(self, tenant_id: UUID) -> dict:
        """Get statistics for the ads alert system"""
        return {
            "total_chats": self.chat_repo.count_by_tenant(tenant_id),
            "subscribed_chats": self.chat_repo.count_by_tenant(tenant_id, subscribed_only=True),
            # Customer-linked chats (invoice customers with Telegram)
            "total_customer_chats": self.chat_repo.count_customer_chats(tenant_id),
            "subscribed_customer_chats": self.chat_repo.count_customer_chats(tenant_id, subscribed_only=True),
            "total_promotions": self.promotion_repo.count_by_tenant(tenant_id),
            "draft_promotions": self.promotion_repo.count_by_tenant(tenant_id, status=PromotionStatus.draft),
            "scheduled_promotions": self.promotion_repo.count_by_tenant(tenant_id, status=PromotionStatus.scheduled),
            "sent_promotions": self.promotion_repo.count_by_tenant(tenant_id, status=PromotionStatus.sent),
            "total_media": len(self.media_repo.get_all_by_tenant(tenant_id)),
            "total_folders": len(self.folder_repo.get_all_by_tenant(tenant_id))
        }


# ==================== Scheduler Functions ====================

async def process_scheduled_promotions(db: Session) -> int:
    """
    Process all scheduled promotions that are due.
    Called by the background scheduler.

    Returns:
        Number of promotions processed
    """
    promotion_repo = AdsAlertPromotionRepository(db)
    due_promotions = promotion_repo.get_due_promotions()

    processed = 0
    for promotion in due_promotions:
        try:
            service = AdsAlertService(db)
            await service.send_promotion_now(promotion.id, promotion.tenant_id)
            processed += 1
            logger.info(f"Processed scheduled promotion: {promotion.id}")
        except Exception as e:
            logger.error(f"Error processing scheduled promotion {promotion.id}: {e}")

    return processed
