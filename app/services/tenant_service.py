# app/services/tenant_service.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.models import Tenant, User, UserRole
from app.repositories import TenantRepository, UserRepository


class TenantService:
    """Service layer for tenant operations"""

    def __init__(self, db: Session):
        self.db = db
        self.tenant_repo = TenantRepository(db)
        self.user_repo = UserRepository(db)

    def create_tenant_with_admin(
        self,
        name: str,
        slug: str,
        admin_telegram_id: str = None,
        admin_email: str = None,
        admin_username: str = None,
        settings: dict = None
    ) -> tuple[Tenant, User]:
        """Create a new tenant with an admin user"""
        # Create tenant
        tenant = self.tenant_repo.create_tenant(name, slug, settings)

        # Create admin user
        admin_user = self.user_repo.create_user(
            tenant_id=tenant.id,
            telegram_user_id=admin_telegram_id,
            email=admin_email,
            username=admin_username,
            role=UserRole.admin
        )

        self.db.commit()
        return tenant, admin_user

    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug"""
        return self.tenant_repo.get_by_slug(slug)

    def get_tenant_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.tenant_repo.get_by_id(tenant_id)

    def get_active_tenants(self) -> List[Tenant]:
        """Get all active tenants"""
        return self.tenant_repo.get_active_tenants()

    def update_tenant_settings(self, tenant_id: UUID, settings: dict) -> Optional[Tenant]:
        """Update tenant settings"""
        tenant = self.tenant_repo.update(tenant_id, settings=settings)
        if tenant:
            self.db.commit()
        return tenant

    def deactivate_tenant(self, tenant_id: UUID) -> Optional[Tenant]:
        """Deactivate a tenant and all related data"""
        tenant = self.tenant_repo.deactivate_tenant(tenant_id)
        if tenant:
            # Deactivate all users in the tenant
            users = self.user_repo.get_tenant_users(tenant_id, active_only=False)
            for user in users:
                self.user_repo.update(user.id, is_active=False)

            self.db.commit()
        return tenant

    def get_tenant_users(self, tenant_id: UUID, active_only: bool = True) -> List[User]:
        """Get all users for a tenant"""
        return self.user_repo.get_tenant_users(tenant_id, active_only)

    def add_user_to_tenant(
        self,
        tenant_id: UUID,
        telegram_user_id: str = None,
        email: str = None,
        username: str = None,
        role: UserRole = UserRole.user
    ) -> User:
        """Add a new user to a tenant"""
        user = self.user_repo.create_user(
            tenant_id=tenant_id,
            telegram_user_id=telegram_user_id,
            email=email,
            username=username,
            role=role
        )
        self.db.commit()
        return user