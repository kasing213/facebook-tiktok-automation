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
        platform_user_id: str,
        active_only: bool = True
    ) -> Optional[SocialIdentity]:
        """Get social identity by platform and platform user ID (e.g., FB user ID)"""
        if active_only:
            return self.find_one_by(
                platform=platform,
                platform_user_id=platform_user_id,
                is_active=True
            )
        else:
            return self.find_one_by(
                platform=platform,
                platform_user_id=platform_user_id
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

        CRITICAL:
        - First checks globally by (platform, platform_user_id) due to unique constraint
        - Then checks by (tenant_id, user_id, platform) for user-specific lookup
        - Always use facebook_user_id for Facebook identities (stable anchor)
        """
        # First: Check if this platform_user_id already exists globally (including inactive)
        # This handles the unique constraint on (platform, platform_user_id)
        existing_global = self.get_by_platform_user_id(platform, platform_user_id, active_only=False)

        if existing_global:
            # Identity exists for this platform user
            if existing_global.user_id == user_id and existing_global.tenant_id == tenant_id:
                # Same user, same tenant - just update
                update_data = {
                    "platform_user_id": platform_user_id,
                    **kwargs
                }
                if facebook_user_id:
                    update_data["facebook_user_id"] = facebook_user_id
                # Reactivate if it was deactivated
                update_data["is_active"] = True
                return self.update(existing_global.id, **update_data)
            elif existing_global.user_id == user_id:
                # Same user, different tenant - update tenant association
                update_data = {
                    "tenant_id": tenant_id,
                    "platform_user_id": platform_user_id,
                    "is_active": True,
                    **kwargs
                }
                if facebook_user_id:
                    update_data["facebook_user_id"] = facebook_user_id
                return self.update(existing_global.id, **update_data)
            else:
                # Different user owns this platform account
                # Transfer ownership to the new user (platform account can only be linked to one user)
                # This happens when someone logs in with a Facebook account previously linked to another user

                # First, check if the new user already has a different identity for this platform
                # If so, deactivate it to avoid violating uq_social_identity_tenant_user_platform
                existing_user_identity = self.get_user_identity(tenant_id, user_id, platform)
                if existing_user_identity and existing_user_identity.id != existing_global.id:
                    self.deactivate(existing_user_identity.id)

                update_data = {
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "platform_user_id": platform_user_id,
                    "is_active": True,
                    **kwargs
                }
                if facebook_user_id:
                    update_data["facebook_user_id"] = facebook_user_id
                return self.update(existing_global.id, **update_data)

        # Second: Check if user already has an identity for this platform
        existing_user = self.get_user_identity(tenant_id, user_id, platform)

        if existing_user:
            # User has a different platform account connected - update to new one
            update_data = {
                "platform_user_id": platform_user_id,
                **kwargs
            }
            if facebook_user_id:
                update_data["facebook_user_id"] = facebook_user_id
            return self.update(existing_user.id, **update_data)

        # No existing identity found - create new
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
