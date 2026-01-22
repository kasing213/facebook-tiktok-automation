# app/routes/ads_alert.py
"""
Ads Alert API routes for promotional messaging system.
"""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import User, PromotionStatus
from app.core.dependencies import get_current_user
from app.core.authorization import get_current_owner, get_current_member_or_owner, require_subscription_feature
from app.schemas.ads_alert import (
    ChatCreate, ChatUpdate, ChatResponse,
    PromotionCreate, PromotionUpdate, PromotionResponse,
    PromotionScheduleRequest, BroadcastResponse,
    FolderCreate, FolderResponse, FolderTreeResponse,
    MediaResponse, MediaUploadResponse, MediaDeleteResponse,
    AdsAlertStats, PromotionStatusEnum, MediaTypeEnum, CustomerTargetTypeEnum
)
from app.core.models import PromotionCustomerTargetType
from app.repositories.ads_alert import (
    AdsAlertChatRepository, AdsAlertPromotionRepository,
    AdsAlertMediaRepository, AdsAlertMediaFolderRepository
)
from app.services.ads_alert_service import AdsAlertService
from app.core.usage_limits import (
    check_promotion_limit, increment_promotion_counter,
    check_broadcast_limit, increment_broadcast_counter
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ads-alert", tags=["ads-alert"])


# ==================== Stats ====================

@router.get("/stats", response_model=AdsAlertStats)
async def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Get statistics for the ads alert system"""
    service = AdsAlertService(db)
    return service.get_stats(current_user.tenant_id)


# ==================== Chat Endpoints ====================

@router.get("/chats", response_model=List[ChatResponse])
async def list_chats(
    subscribed_only: bool = Query(False, description="Filter to subscribed chats only"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """List all registered chats for the tenant"""
    chat_repo = AdsAlertChatRepository(db)
    tags_list = tags.split(",") if tags else None
    chats = chat_repo.get_by_tenant(
        tenant_id=current_user.tenant_id,
        subscribed_only=subscribed_only,
        tags=tags_list,
        limit=limit
    )
    return chats


@router.post("/chats", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    data: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Register a new chat for promotional broadcasts"""
    chat_repo = AdsAlertChatRepository(db)

    # Check if chat already exists
    existing = chat_repo.get_by_chat_id(current_user.tenant_id, data.chat_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Chat with ID '{data.chat_id}' already registered"
        )

    chat = chat_repo.create_with_tenant(
        tenant_id=current_user.tenant_id,
        platform=data.platform,
        chat_id=data.chat_id,
        chat_name=data.chat_name,
        customer_name=data.customer_name,
        tags=data.tags
    )
    db.commit()
    return chat


@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Get a specific chat by ID"""
    chat_repo = AdsAlertChatRepository(db)
    chat = chat_repo.get_by_id_and_tenant(chat_id, current_user.tenant_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.put("/chats/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: UUID,
    data: ChatUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Update a chat registration"""
    chat_repo = AdsAlertChatRepository(db)
    update_data = data.model_dump(exclude_unset=True)
    chat = chat_repo.update_by_tenant(chat_id, current_user.tenant_id, **update_data)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_owner)  # Owner only
):
    """Unregister a chat (soft delete)"""
    chat_repo = AdsAlertChatRepository(db)
    if not chat_repo.soft_delete_by_tenant(chat_id, current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Chat not found")


# ==================== Customer Targeting Endpoints ====================

@router.get("/customers")
async def list_targetable_customers(
    subscribed_only: bool = Query(True, description="Filter to subscribed customers only"),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """
    List invoice customers that can be targeted for promotions.
    Only returns customers with linked Telegram accounts.
    """
    chat_repo = AdsAlertChatRepository(db)
    chats = chat_repo.get_all_customer_chats(
        tenant_id=current_user.tenant_id,
        subscribed_only=subscribed_only
    )

    # Return customer-focused data
    return [
        {
            "customer_id": str(c.customer_id) if c.customer_id else None,
            "customer_name": c.customer_name,
            "chat_id": str(c.id),
            "telegram_chat_id": c.chat_id,
            "subscribed": c.subscribed,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in chats if c.customer_id  # Only include customer-linked chats
    ][:limit]


# ==================== Promotion Endpoints ====================

@router.get("/promotions", response_model=List[PromotionResponse])
async def list_promotions(
    status: Optional[PromotionStatusEnum] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """List all promotions for the tenant"""
    promotion_repo = AdsAlertPromotionRepository(db)
    status_enum = PromotionStatus[status.value] if status else None
    promotions = promotion_repo.get_by_tenant(
        tenant_id=current_user.tenant_id,
        status=status_enum,
        limit=limit
    )
    return promotions


@router.post("/promotions", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED)
@require_subscription_feature('promotion_create')
async def create_promotion(
    data: PromotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Create a new promotion"""
    # Check promotion limit before creating (anti-abuse)
    await check_promotion_limit(current_user.tenant_id, db)

    promotion_repo = AdsAlertPromotionRepository(db)

    # Determine initial status
    initial_status = PromotionStatus.scheduled if data.scheduled_at else PromotionStatus.draft

    promotion = promotion_repo.create_with_tenant(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        title=data.title,
        content=data.content,
        media_urls=data.media_urls,
        media_type=data.media_type.value if data.media_type else "text",
        # Existing chat targeting
        target_type=data.target_type.value if data.target_type else "all",
        target_chat_ids=data.target_chat_ids,
        # Customer-based targeting
        target_customer_type=PromotionCustomerTargetType[data.target_customer_type.value] if data.target_customer_type else PromotionCustomerTargetType.none,
        target_customer_ids=data.target_customer_ids,
        scheduled_at=data.scheduled_at,
        status=initial_status
    )
    db.commit()

    # Increment promotion counter after successful creation
    increment_promotion_counter(current_user.tenant_id, db)

    return promotion


@router.get("/promotions/{promotion_id}", response_model=PromotionResponse)
async def get_promotion(
    promotion_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Get a specific promotion by ID"""
    promotion_repo = AdsAlertPromotionRepository(db)
    promotion = promotion_repo.get_by_id_and_tenant(promotion_id, current_user.tenant_id)
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return promotion


@router.put("/promotions/{promotion_id}", response_model=PromotionResponse)
async def update_promotion(
    promotion_id: UUID,
    data: PromotionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Update a promotion"""
    promotion_repo = AdsAlertPromotionRepository(db)

    # Check if promotion exists
    existing = promotion_repo.get_by_id_and_tenant(promotion_id, current_user.tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Promotion not found")

    # Don't allow editing sent promotions
    if existing.status == PromotionStatus.sent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit a promotion that has already been sent"
        )

    update_data = data.model_dump(exclude_unset=True)

    # Convert enums to appropriate values
    if "media_type" in update_data and update_data["media_type"]:
        update_data["media_type"] = update_data["media_type"].value
    if "target_type" in update_data and update_data["target_type"]:
        update_data["target_type"] = update_data["target_type"].value
    if "status" in update_data and update_data["status"]:
        update_data["status"] = PromotionStatus[update_data["status"].value]
    # Customer-based targeting enum conversion
    if "target_customer_type" in update_data and update_data["target_customer_type"]:
        update_data["target_customer_type"] = PromotionCustomerTargetType[update_data["target_customer_type"].value]

    promotion = promotion_repo.update_by_tenant(promotion_id, current_user.tenant_id, **update_data)
    return promotion


@router.delete("/promotions/{promotion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_promotion(
    promotion_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_owner)  # Owner only
):
    """Delete a promotion"""
    promotion_repo = AdsAlertPromotionRepository(db)
    if not promotion_repo.delete_by_tenant(promotion_id, current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Promotion not found")


@router.post("/promotions/{promotion_id}/send", response_model=BroadcastResponse)
@require_subscription_feature('promotion_send')
async def send_promotion(
    promotion_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Send a promotion immediately to all target chats"""
    # Get promotion and check recipient count before sending (anti-abuse)
    promotion_repo = AdsAlertPromotionRepository(db)
    promotion = promotion_repo.get_by_tenant(promotion_id, current_user.tenant_id)
    if not promotion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")

    # Estimate recipient count for broadcast limit check
    chat_repo = AdsAlertChatRepository(db)
    if promotion.target_type == "all":
        recipient_count = chat_repo.count_active_by_tenant(current_user.tenant_id)
    else:
        recipient_count = len(promotion.target_chat_ids or [])

    # Check broadcast limit before sending (anti-abuse)
    await check_broadcast_limit(current_user.tenant_id, recipient_count, db)

    service = AdsAlertService(db)
    try:
        result = await service.send_promotion_now(promotion_id, current_user.tenant_id)

        # Increment broadcast counter after successful send
        increment_broadcast_counter(current_user.tenant_id, recipient_count, db)

        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/promotions/{promotion_id}/schedule", response_model=PromotionResponse)
async def schedule_promotion(
    promotion_id: UUID,
    data: PromotionScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Schedule a promotion for later sending"""
    service = AdsAlertService(db)
    try:
        promotion = service.schedule_promotion(
            promotion_id,
            current_user.tenant_id,
            data.scheduled_at
        )
        return promotion
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== Folder Endpoints ====================

@router.get("/folders", response_model=List[FolderResponse])
async def list_folders(
    parent_id: Optional[UUID] = Query(None, description="Parent folder ID (null for root)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """List folders, optionally filtered by parent"""
    folder_repo = AdsAlertMediaFolderRepository(db)
    folders = folder_repo.get_by_tenant(
        tenant_id=current_user.tenant_id,
        parent_id=parent_id
    )
    return folders


@router.get("/folders/tree", response_model=List[FolderTreeResponse])
async def get_folder_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Get complete folder tree structure"""
    folder_repo = AdsAlertMediaFolderRepository(db)
    all_folders = folder_repo.get_all_by_tenant(current_user.tenant_id)

    # Build tree structure
    folder_map = {f.id: {"id": f.id, "name": f.name, "parent_id": f.parent_id, "children": []} for f in all_folders}
    root_folders = []

    for folder in all_folders:
        folder_dict = folder_map[folder.id]
        if folder.parent_id and folder.parent_id in folder_map:
            folder_map[folder.parent_id]["children"].append(folder_dict)
        else:
            root_folders.append(folder_dict)

    return root_folders


@router.post("/folders", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    data: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Create a new folder"""
    folder_repo = AdsAlertMediaFolderRepository(db)

    # Verify parent exists if specified
    if data.parent_id:
        parent = folder_repo.get_by_id_and_tenant(data.parent_id, current_user.tenant_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent folder not found")

    try:
        folder = folder_repo.create_with_tenant(
            tenant_id=current_user.tenant_id,
            name=data.name,
            parent_id=data.parent_id,
            created_by=current_user.id
        )
        db.commit()
        return folder
    except Exception as e:
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A folder with this name already exists in the specified location"
            )
        raise


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_owner)  # Owner only
):
    """Delete a folder and its contents"""
    folder_repo = AdsAlertMediaFolderRepository(db)
    if not folder_repo.delete_by_tenant(folder_id, current_user.tenant_id):
        raise HTTPException(status_code=404, detail="Folder not found")


# ==================== Media Endpoints ====================

@router.get("/media", response_model=List[MediaResponse])
async def list_media(
    folder_id: Optional[UUID] = Query(None, description="Folder ID (null for root)"),
    file_type: Optional[str] = Query(None, description="Filter by file type prefix (e.g., 'image/', 'video/')"),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """List media files, optionally filtered by folder"""
    media_repo = AdsAlertMediaRepository(db)
    service = AdsAlertService(db)

    media_list = media_repo.get_by_tenant(
        tenant_id=current_user.tenant_id,
        folder_id=folder_id,
        file_type_prefix=file_type,
        limit=limit
    )

    # Add URLs to response
    result = []
    for media in media_list:
        media_dict = {
            "id": media.id,
            "tenant_id": media.tenant_id,
            "folder_id": media.folder_id,
            "filename": media.filename,
            "original_filename": media.original_filename,
            "storage_path": media.storage_path,
            "url": service.get_media_url(media.storage_path),
            "file_type": media.file_type,
            "file_size": media.file_size,
            "thumbnail_url": service.get_media_url(media.thumbnail_path) if media.thumbnail_path else None,
            "width": media.width,
            "height": media.height,
            "duration": media.duration,
            "created_by": media.created_by,
            "created_at": media.created_at
        }
        result.append(media_dict)

    return result


@router.get("/media/search", response_model=List[MediaResponse])
async def search_media(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Search media by filename"""
    media_repo = AdsAlertMediaRepository(db)
    service = AdsAlertService(db)

    media_list = media_repo.search_by_filename(
        tenant_id=current_user.tenant_id,
        search_term=q,
        limit=limit
    )

    # Add URLs to response
    result = []
    for media in media_list:
        media_dict = {
            "id": media.id,
            "tenant_id": media.tenant_id,
            "folder_id": media.folder_id,
            "filename": media.filename,
            "original_filename": media.original_filename,
            "storage_path": media.storage_path,
            "url": service.get_media_url(media.storage_path),
            "file_type": media.file_type,
            "file_size": media.file_size,
            "thumbnail_url": service.get_media_url(media.thumbnail_path) if media.thumbnail_path else None,
            "width": media.width,
            "height": media.height,
            "duration": media.duration,
            "created_by": media.created_by,
            "created_at": media.created_at
        }
        result.append(media_dict)

    return result


@router.post("/media/upload", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    folder_id: Optional[UUID] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """Upload a media file"""
    # Validate file type
    allowed_types = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "video/mp4", "video/webm", "video/quicktime",
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' not allowed. Allowed types: {', '.join(allowed_types)}"
        )

    # Read file content
    content = await file.read()

    # Check file size (max 50MB)
    max_size = 50 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of 50MB"
        )

    service = AdsAlertService(db)

    try:
        media = await service.upload_media(
            tenant_id=current_user.tenant_id,
            file_content=content,
            filename=file.filename,
            content_type=file.content_type,
            folder_id=folder_id,
            created_by=current_user.id
        )
        db.commit()

        return {
            "id": media.id,
            "filename": media.filename,
            "storage_path": media.storage_path,
            "url": service.get_media_url(media.storage_path),
            "file_type": media.file_type,
            "file_size": media.file_size
        }
    except Exception as e:
        logger.error(f"Error uploading media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload media file"
        )


@router.delete("/media/{media_id}", response_model=MediaDeleteResponse)
async def delete_media(
    media_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_owner)  # Owner only
):
    """Delete a media file"""
    media_repo = AdsAlertMediaRepository(db)
    media = media_repo.get_by_id_and_tenant(media_id, current_user.tenant_id)

    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    service = AdsAlertService(db)
    await service.delete_media(media_id, current_user.tenant_id)

    return {
        "id": media_id,
        "filename": media.filename,
        "deleted": True
    }


@router.get("/media/file/{file_id}")
async def get_media_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_member_or_owner)
):
    """
    Stream media file from MongoDB GridFS.

    The file_id is the GridFS ObjectId string stored in the media record's storage_path field.
    """
    service = AdsAlertService(db)

    # Get file from GridFS with tenant validation
    result = await service.storage_service.get_file(file_id, current_user.tenant_id)

    if not result:
        raise HTTPException(status_code=404, detail="File not found")

    content, content_type, filename = result

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "public, max-age=31536000"  # 1 year cache
        }
    )
