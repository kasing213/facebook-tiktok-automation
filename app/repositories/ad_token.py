# app/repositories/ad_token.py
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.models import AdToken, Platform
from .base import BaseRepository


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
        account_ref: str = None,
        user_id: Optional[UUID] = None
    ) -> Optional[AdToken]:
        """Get active token for platform and optionally specific account"""
        filters = {
            "tenant_id": tenant_id,
            "platform": platform,
            "is_valid": True
        }
        if account_ref:
            filters["account_ref"] = account_ref
        if user_id is not None:
            filters["user_id"] = user_id

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
        user_id: UUID = None,
        account_ref: str = None,
        account_name: str = None,
        refresh_token_enc: str = None,
        scope: str = None,
        expires_at: datetime = None,
        meta: dict = None
    ) -> AdToken:
        """Create a new ad token"""
        return self.create(
            tenant_id=tenant_id,
            user_id=user_id,
            platform=platform,
            account_ref=account_ref,
            account_name=account_name,
            access_token_enc=access_token_enc,
            refresh_token_enc=refresh_token_enc,
            scope=scope,
            expires_at=expires_at,
            is_valid=True,
            meta=meta or {}
        )

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
        user_id: Optional[UUID] = None
    ) -> List[AdToken]:
        """Get all tokens for a tenant"""
        filters = {"tenant_id": tenant_id}
        if valid_only:
            filters["is_valid"] = True
        if user_id is not None:
            filters["user_id"] = user_id
        return self.find_by(**filters)
