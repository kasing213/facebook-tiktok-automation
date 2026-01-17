# app/repositories/password_reset.py
"""
Repository for password reset token operations.
"""
import datetime as dt
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.models import PasswordResetToken


class PasswordResetRepository:
    """Repository for password reset token database operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_token(self, token_hash: str) -> Optional[PasswordResetToken]:
        """Get a password reset token by its hash"""
        return self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token_hash
        ).first()

    def create_token(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: dt.datetime
    ) -> PasswordResetToken:
        """Create a new password reset token"""
        token = PasswordResetToken(
            user_id=user_id,
            token=token_hash,
            expires_at=expires_at
        )
        self.db.add(token)
        return token

    def mark_as_used(self, token_id: UUID) -> None:
        """Mark a token as used"""
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.id == token_id
        ).update({
            "used_at": dt.datetime.now(dt.timezone.utc)
        })

    def invalidate_user_tokens(self, user_id: UUID) -> int:
        """Invalidate all existing tokens for a user (mark as used)"""
        now = dt.datetime.now(dt.timezone.utc)
        result = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None)
        ).update({
            "used_at": now
        })
        return result

    def cleanup_expired(self) -> int:
        """Delete expired tokens (maintenance task)"""
        now = dt.datetime.now(dt.timezone.utc)
        result = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at < now
        ).delete()
        return result

    def get_recent_token_for_user(self, user_id: UUID, minutes: int = 10) -> Optional[PasswordResetToken]:
        """Check if user has a recent token (for rate limiting)"""
        threshold = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=minutes)
        return self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.created_at > threshold,
            PasswordResetToken.used_at.is_(None)
        ).first()
