# app/repositories/email_verification.py
"""
Repository for email verification token operations.
"""
from typing import Optional
from uuid import UUID
import datetime as dt
from sqlalchemy.orm import Session
from app.core.models import EmailVerificationToken
from .base import BaseRepository


class EmailVerificationRepository(BaseRepository[EmailVerificationToken]):
    """Repository for email verification token operations"""

    def __init__(self, db: Session):
        super().__init__(db, EmailVerificationToken)

    def get_by_token(self, token_hash: str) -> Optional[EmailVerificationToken]:
        """Get verification token by hash"""
        return self.find_one_by(token=token_hash)

    def create_token(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: dt.datetime
    ) -> EmailVerificationToken:
        """Create a new email verification token"""
        return self.create(
            user_id=user_id,
            token=token_hash,
            expires_at=expires_at
        )

    def mark_as_used(self, token_id: UUID) -> Optional[EmailVerificationToken]:
        """Mark token as used"""
        return self.update(token_id, used_at=dt.datetime.now(dt.timezone.utc))

    def invalidate_user_tokens(self, user_id: UUID) -> int:
        """Invalidate all existing tokens for a user (called before creating new one)"""
        now = dt.datetime.now(dt.timezone.utc)
        result = self.db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > now
        ).update({"used_at": now})
        return result

    def cleanup_expired(self) -> int:
        """Delete expired tokens (for cleanup job)"""
        now = dt.datetime.now(dt.timezone.utc)
        result = self.db.query(EmailVerificationToken).filter(
            EmailVerificationToken.expires_at < now
        ).delete()
        return result
