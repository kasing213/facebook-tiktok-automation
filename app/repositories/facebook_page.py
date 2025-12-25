# app/repositories/facebook_page.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.models import FacebookPage
from .base import BaseRepository


class FacebookPageRepository(BaseRepository[FacebookPage]):
    """Repository for Facebook page operations"""

    def __init__(self, db: Session):
        super().__init__(db, FacebookPage)

    def get_by_page_id(self, page_id: str) -> Optional[FacebookPage]:
        """Get page by Facebook page ID (globally unique)"""
        return self.find_one_by(page_id=page_id, is_active=True)

    def get_identity_pages(self, social_identity_id: UUID) -> List[FacebookPage]:
        """Get all active pages for a social identity"""
        return self.find_by(
            social_identity_id=social_identity_id,
            is_active=True
        )

    def get_user_pages(
        self,
        tenant_id: UUID,
        user_id: UUID
    ) -> List[FacebookPage]:
        """Get all pages managed by a user via their social identity"""
        from app.core.models import SocialIdentity, Platform

        # Join through social_identity to filter by user
        pages = (
            self.db.query(FacebookPage)
            .join(SocialIdentity, FacebookPage.social_identity_id == SocialIdentity.id)
            .filter(
                SocialIdentity.tenant_id == tenant_id,
                SocialIdentity.user_id == user_id,
                SocialIdentity.platform == Platform.facebook,
                SocialIdentity.is_active == True,
                FacebookPage.is_active == True
            )
            .all()
        )
        return pages

    def create_or_update(
        self,
        social_identity_id: UUID,
        page_id: str,
        name: str,
        **kwargs
    ) -> FacebookPage:
        """
        Create new or update existing Facebook page (upsert pattern)

        Page ID is globally unique across all users/tenants
        """
        existing = self.get_by_page_id(page_id)

        if existing:
            # Update existing page
            # IMPORTANT: Keep same social_identity_id (don't allow page ownership transfer)
            return self.update(
                existing.id,
                name=name,
                **kwargs
            )
        else:
            # Create new page
            return self.create(
                social_identity_id=social_identity_id,
                page_id=page_id,
                name=name,
                **kwargs
            )

    def deactivate(self, page_id_or_uuid: str | UUID) -> Optional[FacebookPage]:
        """Deactivate a Facebook page (soft delete at page level)"""
        if isinstance(page_id_or_uuid, str) and not page_id_or_uuid.count('-') == 4:
            # It's a Facebook page ID (not UUID)
            page = self.get_by_page_id(page_id_or_uuid)
            if page:
                return self.update(page.id, is_active=False)
            return None
        else:
            # It's a UUID
            return self.update(UUID(page_id_or_uuid) if isinstance(page_id_or_uuid, str) else page_id_or_uuid, is_active=False)

    def reactivate(self, page_id_or_uuid: str | UUID) -> Optional[FacebookPage]:
        """Reactivate a previously deactivated Facebook page"""
        if isinstance(page_id_or_uuid, str) and not page_id_or_uuid.count('-') == 4:
            page = self.find_one_by(page_id=page_id_or_uuid)  # Don't filter by is_active
            if page:
                return self.update(page.id, is_active=True)
            return None
        else:
            return self.update(UUID(page_id_or_uuid) if isinstance(page_id_or_uuid, str) else page_id_or_uuid, is_active=True)
