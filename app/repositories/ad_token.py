# app/repositories/ad_token.py
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.core.models import AdToken, Platform, TokenType
from .base import BaseRepository

logger = logging.getLogger(__name__)


class AdTokenRepository(BaseRepository[AdToken]):
    """Repository for ad token operations"""

    def __init__(self, db: Session):
        super().__init__(db, AdToken)

    def get_by_platform(
        self,
        tenant_id: UUID,
        platform: Platform,
        user_id: Optional[UUID] = None
    ) -> List[AdToken]:
        """Get all tokens for a specific platform and tenant"""
        filters = {"tenant_id": tenant_id, "platform": platform}
        if user_id is not None:
            filters["user_id"] = user_id
        return self.find_by(**filters)

    def get_active_token(
        self,
        tenant_id: UUID,
        platform: Platform,
        user_id: UUID,  # NOW REQUIRED - not Optional
        account_ref: str = None,
        social_identity_id: Optional[UUID] = None,
        facebook_page_id: Optional[UUID] = None
    ) -> Optional[AdToken]:
        """
        Get active token for platform and user

        CRITICAL: user_id is REQUIRED - prevents cross-user token leakage
        """
        if user_id is None:
            raise ValueError("user_id is required and cannot be None")

        filters = {
            "tenant_id": tenant_id,
            "platform": platform,
            "user_id": user_id,  # ALWAYS included now
            "is_valid": True,
            "deleted_at": None  # Filter out soft-deleted tokens
        }

        if account_ref:
            filters["account_ref"] = account_ref
        if social_identity_id:
            filters["social_identity_id"] = social_identity_id
        if facebook_page_id:
            filters["facebook_page_id"] = facebook_page_id

        tokens = self.find_by(**filters)
        if not tokens:
            return None

        # Return the most recently updated valid token
        return max(tokens, key=lambda t: t.updated_at)

    def get_expiring_tokens(self, hours_ahead: int = 24) -> List[AdToken]:
        """Get tokens that will expire within specified hours"""
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() + timedelta(hours=hours_ahead)

        return (
            self.db.query(AdToken)
            .filter(
                AdToken.expires_at.isnot(None),
                AdToken.expires_at <= cutoff,
                AdToken.is_valid == True
            )
            .all()
        )

    def create_token(
        self,
        tenant_id: UUID,
        platform: Platform,
        access_token_enc: str,
        user_id: UUID,  # NOW REQUIRED - not Optional
        social_identity_id: Optional[UUID] = None,
        facebook_page_id: Optional[UUID] = None,
        token_type: TokenType = TokenType.user,
        account_ref: str = None,
        account_name: str = None,
        refresh_token_enc: str = None,
        scope: str = None,
        expires_at: datetime = None,
        meta: dict = None
    ) -> AdToken:
        """
        Create a new ad token

        CRITICAL: user_id is REQUIRED - enforces per-user ownership
        """
        if user_id is None:
            raise ValueError("user_id is required and cannot be None")

        logger.info(f"AdTokenRepository.create_token called with token_type={token_type}, facebook_page_id={facebook_page_id}")

        token = self.create(
            tenant_id=tenant_id,
            user_id=user_id,
            platform=platform,
            social_identity_id=social_identity_id,
            facebook_page_id=facebook_page_id,
            token_type=token_type,
            account_ref=account_ref,
            account_name=account_name,
            access_token_enc=access_token_enc,
            refresh_token_enc=refresh_token_enc,
            scope=scope,
            expires_at=expires_at,
            is_valid=True,
            deleted_at=None,
            meta=meta or {}
        )

        logger.info(f"AdTokenRepository.create_token created token: id={token.id}, token_type={token.token_type}, facebook_page_id={token.facebook_page_id}")
        return token

    def invalidate_token(self, token_id: UUID) -> Optional[AdToken]:
        """Mark a token as invalid"""
        return self.update(token_id, is_valid=False)

    def update_validation(self, token_id: UUID, is_valid: bool = True) -> Optional[AdToken]:
        """Update token validation status and timestamp"""
        return self.update(
            token_id,
            is_valid=is_valid,
            last_validated=datetime.utcnow()
        )

    def get_tenant_tokens(
        self,
        tenant_id: UUID,
        valid_only: bool = True,
        user_id: Optional[UUID] = None,
        include_deleted: bool = False
    ) -> List[AdToken]:
        """Get all tokens for a tenant"""
        filters = {"tenant_id": tenant_id}
        if valid_only:
            filters["is_valid"] = True
        if user_id is not None:
            filters["user_id"] = user_id
        if not include_deleted:
            filters["deleted_at"] = None
        return self.find_by(**filters)

    def soft_delete(self, token_id: UUID) -> Optional[AdToken]:
        """
        Soft delete a token (set deleted_at timestamp)

        CRITICAL: Preserves forensic trail instead of hard delete
        """
        return self.update(token_id, deleted_at=datetime.utcnow())

    def verify_user_owns_token(self, token_id: UUID, user_id: UUID) -> bool:
        """
        Verify that a user owns a specific token

        Returns: True if user owns token and it's not deleted, False otherwise
        """
        token = self.get_by_id(token_id)
        return (
            token is not None
            and token.user_id == user_id
            and token.deleted_at is None
        )

    def get_user_tokens_by_type(
        self,
        tenant_id: UUID,
        user_id: UUID,
        token_type: TokenType,
        valid_only: bool = True
    ) -> List[AdToken]:
        """Get all tokens of a specific type for a user"""
        filters = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "token_type": token_type,
            "deleted_at": None
        }
        if valid_only:
            filters["is_valid"] = True
        return self.find_by(**filters)
