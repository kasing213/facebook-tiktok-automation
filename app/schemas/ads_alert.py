# app/schemas/ads_alert.py
"""Pydantic schemas for Ads Alert system"""
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


# Enums for API
class PromotionStatusEnum(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    sent = "sent"
    cancelled = "cancelled"


class MediaTypeEnum(str, Enum):
    text = "text"
    image = "image"
    video = "video"
    document = "document"
    mixed = "mixed"


class TargetTypeEnum(str, Enum):
    all = "all"
    selected = "selected"


class BroadcastStatusEnum(str, Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


# Chat Schemas
class ChatCreate(BaseModel):
    """Create a new chat registration"""
    platform: str = "telegram"
    chat_id: str = Field(..., min_length=1, max_length=100)
    chat_name: Optional[str] = None
    customer_name: Optional[str] = None
    tags: List[str] = []


class ChatUpdate(BaseModel):
    """Update chat registration"""
    chat_name: Optional[str] = None
    customer_name: Optional[str] = None
    tags: Optional[List[str]] = None
    subscribed: Optional[bool] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    id: UUID
    tenant_id: UUID
    platform: str
    chat_id: str
    chat_name: Optional[str]
    customer_name: Optional[str]
    tags: List[str]
    subscribed: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Promotion Schemas
class PromotionCreate(BaseModel):
    """Create a new promotion"""
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    media_urls: List[str] = []
    media_type: MediaTypeEnum = MediaTypeEnum.text
    target_type: TargetTypeEnum = TargetTypeEnum.all
    target_chat_ids: List[UUID] = []
    scheduled_at: Optional[datetime] = None


class PromotionUpdate(BaseModel):
    """Update promotion"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    media_urls: Optional[List[str]] = None
    media_type: Optional[MediaTypeEnum] = None
    target_type: Optional[TargetTypeEnum] = None
    target_chat_ids: Optional[List[UUID]] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[PromotionStatusEnum] = None


class PromotionResponse(BaseModel):
    """Promotion response model"""
    id: UUID
    tenant_id: UUID
    title: str
    content: Optional[str]
    status: PromotionStatusEnum
    media_urls: List[str]
    media_type: MediaTypeEnum
    scheduled_at: Optional[datetime]
    target_type: TargetTypeEnum
    target_chat_ids: List[UUID]
    sent_at: Optional[datetime]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromotionSendRequest(BaseModel):
    """Request to send a promotion immediately"""
    pass  # No additional fields needed


class PromotionScheduleRequest(BaseModel):
    """Request to schedule a promotion"""
    scheduled_at: datetime


# Media Folder Schemas
class FolderCreate(BaseModel):
    """Create a new folder"""
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[UUID] = None


class FolderResponse(BaseModel):
    """Folder response model"""
    id: UUID
    tenant_id: UUID
    name: str
    parent_id: Optional[UUID]
    created_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class FolderTreeResponse(BaseModel):
    """Folder with children for tree view"""
    id: UUID
    name: str
    parent_id: Optional[UUID]
    children: List["FolderTreeResponse"] = []

    class Config:
        from_attributes = True


# Update forward reference
FolderTreeResponse.model_rebuild()


# Media Schemas
class MediaResponse(BaseModel):
    """Media file response model"""
    id: UUID
    tenant_id: UUID
    folder_id: Optional[UUID]
    filename: str
    original_filename: Optional[str]
    storage_path: str
    url: str  # Computed public URL
    file_type: str
    file_size: Optional[int]
    thumbnail_url: Optional[str]  # Computed thumbnail URL
    width: Optional[int]
    height: Optional[int]
    duration: Optional[int]
    created_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class MediaUploadResponse(BaseModel):
    """Response after uploading media"""
    id: UUID
    filename: str
    storage_path: str
    url: str
    file_type: str
    file_size: int


class MediaDeleteResponse(BaseModel):
    """Response after deleting media"""
    id: UUID
    filename: str
    deleted: bool


# Broadcast Schemas
class BroadcastRequest(BaseModel):
    """Request to broadcast to multiple chats"""
    chat_ids: List[str]  # Telegram chat IDs (strings)
    content: str
    media_type: MediaTypeEnum = MediaTypeEnum.text
    media_urls: List[str] = []


class BroadcastResult(BaseModel):
    """Result of broadcasting to a single chat"""
    chat_id: str
    success: bool
    error: Optional[str] = None


class BroadcastResponse(BaseModel):
    """Response after broadcasting"""
    promotion_id: UUID
    total: int
    sent: int
    failed: int
    results: List[BroadcastResult]


class BroadcastLogResponse(BaseModel):
    """Broadcast log entry response"""
    id: UUID
    promotion_id: UUID
    chat_id: UUID
    status: BroadcastStatusEnum
    error_message: Optional[str]
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Stats Schemas
class AdsAlertStats(BaseModel):
    """Statistics for ads alert system"""
    total_chats: int
    subscribed_chats: int
    total_promotions: int
    draft_promotions: int
    scheduled_promotions: int
    sent_promotions: int
    total_media: int
    total_folders: int
