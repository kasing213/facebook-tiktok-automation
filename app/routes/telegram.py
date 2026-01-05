# app/routes/telegram.py
"""
Telegram integration routes for user account linking.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import get_settings
from app.core.models import User
from app.repositories import TelegramRepository
from app.routes.auth import get_current_user

router = APIRouter(prefix="/telegram", tags=["telegram"])


# Request/Response Models
class LinkCodeResponse(BaseModel):
    """Link code generation response"""
    code: str
    expires_at: datetime
    bot_url: str
    deep_link: str


class TelegramStatusResponse(BaseModel):
    """Telegram connection status response"""
    connected: bool
    telegram_user_id: Optional[str] = None
    telegram_username: Optional[str] = None
    linked_at: Optional[datetime] = None


class VerifyCodeRequest(BaseModel):
    """Verify link code request (for bot/gateway use)"""
    code: str
    telegram_user_id: str
    telegram_username: Optional[str] = None


class VerifyCodeResponse(BaseModel):
    """Verify code response"""
    success: bool
    user_id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None
    username: Optional[str] = None
    email: Optional[str] = None
    message: str


class DisconnectResponse(BaseModel):
    """Disconnect telegram response"""
    success: bool
    message: str


# Routes
@router.post("/generate-code", response_model=LinkCodeResponse)
async def generate_link_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a temporary code for linking Telegram account.

    The user should send this code to the Telegram bot using /start <code>
    to link their Telegram account to this dashboard account.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Link code with expiration and bot URL
    """
    telegram_repo = TelegramRepository(db)

    # Generate new link code (15 min expiry)
    link_code = telegram_repo.create_link_code(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        expiry_minutes=15
    )
    db.commit()

    # Build bot URLs
    settings = get_settings()
    bot_username = getattr(settings, "TELEGRAM_BOT_USERNAME", "your_bot")
    bot_url = f"https://t.me/{bot_username}"
    deep_link = f"https://t.me/{bot_username}?start={link_code.code}"

    return LinkCodeResponse(
        code=link_code.code,
        expires_at=link_code.expires_at,
        bot_url=bot_url,
        deep_link=deep_link
    )


@router.get("/status", response_model=TelegramStatusResponse)
async def get_telegram_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Telegram connection status for current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Telegram connection status
    """
    telegram_repo = TelegramRepository(db)
    status_data = telegram_repo.get_user_telegram_status(current_user.id)

    return TelegramStatusResponse(**status_data)


@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect_telegram(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect Telegram account from dashboard.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Disconnect result
    """
    telegram_repo = TelegramRepository(db)

    # Check if connected
    status_data = telegram_repo.get_user_telegram_status(current_user.id)
    if not status_data["connected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Telegram account connected"
        )

    success = telegram_repo.disconnect_telegram(current_user.id)
    db.commit()

    if success:
        return DisconnectResponse(
            success=True,
            message="Telegram account disconnected successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Telegram account"
        )


@router.post("/verify-code", response_model=VerifyCodeResponse)
async def verify_link_code(
    request: VerifyCodeRequest,
    db: Session = Depends(get_db)
):
    """
    Verify and consume a link code (for bot/gateway use).

    This endpoint is called by the Telegram bot or API gateway
    when a user sends /start <code> to link their account.

    Note: This endpoint should be protected by API key in production.

    Args:
        request: Code verification request with Telegram user info
        db: Database session

    Returns:
        Verification result with user info if successful
    """
    telegram_repo = TelegramRepository(db)

    # Check if code is valid
    link_code = telegram_repo.get_valid_code(request.code)
    if not link_code:
        return VerifyCodeResponse(
            success=False,
            message="Invalid or expired code"
        )

    # Consume the code and link Telegram
    user = telegram_repo.consume_code(
        code=request.code,
        telegram_user_id=request.telegram_user_id,
        telegram_username=request.telegram_username
    )
    db.commit()

    if user:
        return VerifyCodeResponse(
            success=True,
            user_id=user.id,
            tenant_id=user.tenant_id,
            username=user.username,
            email=user.email,
            message="Telegram account linked successfully"
        )
    else:
        return VerifyCodeResponse(
            success=False,
            message="Failed to link Telegram account"
        )


@router.get("/user/{telegram_user_id}")
async def get_user_by_telegram_id(
    telegram_user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user by Telegram user ID (for bot/gateway use).

    Note: This endpoint should be protected by API key in production.

    Args:
        telegram_user_id: Telegram user ID
        db: Database session

    Returns:
        User info if found
    """
    telegram_repo = TelegramRepository(db)
    user = telegram_repo.get_user_by_telegram_id(telegram_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user linked to this Telegram account"
        )

    return {
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "username": user.username,
        "email": user.email,
        "telegram_user_id": user.telegram_user_id,
        "telegram_username": user.telegram_username,
        "telegram_linked_at": user.telegram_linked_at.isoformat() if user.telegram_linked_at else None
    }


@router.post("/cleanup-expired")
async def cleanup_expired_codes(
    db: Session = Depends(get_db)
):
    """
    Clean up expired link codes (admin/maintenance endpoint).

    Note: This endpoint should be protected by admin authentication.

    Args:
        db: Database session

    Returns:
        Number of codes deleted
    """
    telegram_repo = TelegramRepository(db)
    deleted_count = telegram_repo.cleanup_expired_codes()
    db.commit()

    return {
        "success": True,
        "deleted_count": deleted_count,
        "message": f"Cleaned up {deleted_count} expired link codes"
    }


@router.get("/debug-config")
async def debug_config():
    """
    Debug endpoint to check config values.

    This shows what value TELEGRAM_BOT_USERNAME has at runtime.
    Remove this endpoint after debugging.
    """
    import os
    settings = get_settings()
    return {
        "env_var_direct": os.environ.get("TELEGRAM_BOT_USERNAME", "NOT_SET"),
        "settings_value": settings.TELEGRAM_BOT_USERNAME,
        "all_telegram_vars": {
            k: v for k, v in os.environ.items()
            if "TELEGRAM" in k.upper()
        }
    }
