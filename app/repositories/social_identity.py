# app/repositories/social_identity.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.models import SocialIdentity, Platform
from .base import BaseRepository


class SocialIdentityRepository(BaseRepository[SocialIdentity]):
    """Repository for social identity operations with per-user isolation"""

    def __init__(self, db: Session):
        super().__init__(db, SocialIdentity)

    def get_by_platform_user_id(
        self,
        platform: Platform,
        platform_user_id: str
    ) -> Optional[SocialIdentity]:
        """Get social identity by platform and platform user ID (e.g., FB user ID)"""
        return self.find_one_by(
            platform=platform,
            platform_user_id=platform_user_id,
            is_active=True
        )

    def get_by_facebook_user_id(
        self,
        facebook_user_id: str
    ) -> Optional[SocialIdentity]:
        """Get social identity by real Facebook user ID (stable anchor)"""
        return self.find_one_by(
            platform=Platform.facebook,
            facebook_user_id=facebook_user_id,
            is_active=True
        )

    def get_user_identity(
        self,
        tenant_id: UUID,
        user_id: UUID,
        platform: Platform
    ) -> Optional[SocialIdentity]:
        """Get user's identity for a specific platform"""
        return self.find_one_by(
            tenant_id=tenant_id,
            user_id=user_id,
            platform=platform,
            is_active=True
        )

    def get_user_identities(
        self,
        tenant_id: UUID,
        user_id: UUID
    ) -> List[SocialIdentity]:
        """Get all active social identities for a user"""
        return self.find_by(
            tenant_id=tenant_id,
            user_id=user_id,
            is_active=True
        )

    def create_or_update(
        self,
        tenant_id: UUID,
        user_id: UUID,
        platform: Platform,
        platform_user_id: str,
        facebook_user_id: Optional[str] = None,
        **kwargs
    ) -> SocialIdentity:
        """
        Create new or update existing social identity (upsert pattern)

        CRITICAL: Always use facebook_user_id for Facebook identities (stable anchor)
        """
        existing = self.get_user_identity(tenant_id, user_id, platform)

        if existing:
            # Update existing identity
            update_data = {
                "platform_user_id": platform_user_id,
                **kwargs
            }

            # CRITICAL: Always update facebook_user_id if provided
            if facebook_user_id:
                update_data["facebook_user_id"] = facebook_user_id

            return self.update(existing.id, **update_data)
        else:
            # Create new identity
            return self.create(
                tenant_id=tenant_id,
                user_id=user_id,
                platform=platform,
                platform_user_id=platform_user_id,
                facebook_user_id=facebook_user_id,
                **kwargs
            )

    def deactivate(self, identity_id: UUID) -> Optional[SocialIdentity]:
        """Deactivate a social identity (soft delete at identity level)"""
        return self.update(identity_id, is_active=False)

    def reactivate(self, identity_id: UUID) -> Optional[SocialIdentity]:
        """Reactivate a previously deactivated social identity"""
        return self.update(identity_id, is_active=True)
