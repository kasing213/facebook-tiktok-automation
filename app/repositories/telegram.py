# app/repositories/telegram.py
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.models import TelegramLinkCode, User
from .base import BaseRepository


class TelegramRepository(BaseRepository[TelegramLinkCode]):
    """Repository for Telegram link code operations"""

    def __init__(self, db: Session):
        super().__init__(db, TelegramLinkCode)

    def create_link_code(
        self,
        user_id: UUID,
        tenant_id: UUID,
        expiry_minutes: int = 15
    ) -> TelegramLinkCode:
        """Generate a unique link code for connecting Telegram account"""
        # Generate a URL-safe random code (24 characters)
        code = secrets.token_urlsafe(18)[:24]

        # Ensure uniqueness
        while self.get_valid_code(code):
            code = secrets.token_urlsafe(18)[:24]

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)

        return self.create(
            user_id=user_id,
            tenant_id=tenant_id,
            code=code,
            expires_at=expires_at
        )

    def get_valid_code(self, code: str) -> Optional[TelegramLinkCode]:
        """Get a link code if it's valid (not expired and not used)"""
        return self.db.query(TelegramLinkCode).filter(
            TelegramLinkCode.code == code,
            TelegramLinkCode.expires_at > datetime.now(timezone.utc),
            TelegramLinkCode.used_at.is_(None)
        ).first()

    def consume_code(
        self,
        code: str,
        telegram_user_id: str,
        telegram_username: Optional[str] = None
    ) -> Optional[User]:
        """
        Mark code as used and link Telegram account to user.
        Returns the updated User if successful, None otherwise.

        Handles the case where Telegram ID is already linked to another user
        by unlinking it from the previous user first.
        """
        from sqlalchemy.exc import IntegrityError

        link_code = self.get_valid_code(code)
        if not link_code:
            return None

        # Get the target user
        user = self.db.query(User).filter(User.id == link_code.user_id).first()
        if not user:
            return None

        try:
            # Check if this Telegram ID is already linked to another user in this tenant
            existing_user = self.db.query(User).filter(
                User.telegram_user_id == telegram_user_id,
                User.tenant_id == user.tenant_id,
                User.id != user.id  # Exclude current user
            ).first()

            if existing_user:
                # Unlink from previous user first
                existing_user.telegram_user_id = None
                existing_user.telegram_username = None
                existing_user.telegram_linked_at = None
                self.db.flush()

            # Mark code as used
            now = datetime.now(timezone.utc)
            link_code.used_at = now
            link_code.telegram_user_id = telegram_user_id

            # Link to new user
            user.telegram_user_id = telegram_user_id
            user.telegram_username = telegram_username
            user.telegram_linked_at = now

            self.db.flush()
            self.db.refresh(user)

            return user

        except IntegrityError as e:
            # Handle any remaining constraint violations
            self.db.rollback()

            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Telegram linking constraint violation: {e}")

            return None

    def get_user_telegram_status(self, user_id: UUID) -> Dict[str, Any]:
        """Get Telegram connection status for a user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"connected": False}

        return {
            "connected": user.telegram_user_id is not None,
            "telegram_username": user.telegram_username,
            "telegram_user_id": user.telegram_user_id,
            "linked_at": user.telegram_linked_at.isoformat() if user.telegram_linked_at else None
        }

    def disconnect_telegram(self, user_id: UUID) -> bool:
        """Remove Telegram link from user account"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        user.telegram_user_id = None
        user.telegram_username = None
        user.telegram_linked_at = None
        self.db.flush()
        return True

    def get_user_by_telegram_id(self, telegram_user_id: str) -> Optional[User]:
        """Find a user by their linked Telegram ID"""
        return self.db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()

    def cleanup_expired_codes(self) -> int:
        """Delete expired link codes. Returns count of deleted records."""
        result = self.db.query(TelegramLinkCode).filter(
            TelegramLinkCode.expires_at < datetime.now(timezone.utc)
        ).delete()
        self.db.flush()
        return result
