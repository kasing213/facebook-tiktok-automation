# app/repositories/tenant.py
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.models import Tenant
from .base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for tenant operations"""

    def __init__(self, db: Session):
        super().__init__(db, Tenant)

    def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug"""
        return self.find_one_by(slug=slug)

    def get_active_tenants(self) -> List[Tenant]:
        """Get all active tenants"""
        return self.find_by(is_active=True)

    def create_tenant(self, name: str, slug: str, settings: dict = None) -> Tenant:
        """Create a new tenant with validation"""
        if self.get_by_slug(slug):
            raise ValueError(f"Tenant with slug '{slug}' already exists")

        return self.create(
            name=name,
            slug=slug,
            is_active=True,
            settings=settings or {}
        )

    def deactivate_tenant(self, tenant_id) -> Optional[Tenant]:
        """Deactivate a tenant instead of deleting"""
        return self.update(tenant_id, is_active=False)