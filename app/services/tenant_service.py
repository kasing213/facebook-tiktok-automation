# app/services/tenant_service.py
import logging
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.models import Tenant, User, UserRole
from app.repositories import TenantRepository, UserRepository

logger = logging.getLogger(__name__)


class TenantServiceError(Exception):
    """Base exception for tenant service errors"""
    pass


class TenantCreationError(TenantServiceError):
    """Raised when tenant creation fails"""
    pass


class TenantNotFoundError(TenantServiceError):
    """Raised when a tenant is not found"""
    pass


class UserCreationError(TenantServiceError):
    """Raised when user creation fails"""
    pass


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
        try:
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
            logger.info(f"Created tenant '{name}' (slug: {slug}) with admin user")
            return tenant, admin_user

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating tenant '{name}': {e}")
            raise TenantCreationError(f"Tenant with slug '{slug}' already exists or duplicate data")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating tenant '{name}': {e}")
            raise TenantCreationError(f"Failed to create tenant: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating tenant '{name}': {e}")
            raise TenantCreationError(f"Unexpected error: {str(e)}")

    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug"""
        try:
            return self.tenant_repo.get_by_slug(slug)
        except SQLAlchemyError as e:
            logger.error(f"Database error getting tenant by slug '{slug}': {e}")
            raise TenantServiceError(f"Failed to retrieve tenant: {str(e)}")

    def get_tenant_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID"""
        try:
            return self.tenant_repo.get_by_id(tenant_id)
        except SQLAlchemyError as e:
            logger.error(f"Database error getting tenant by ID '{tenant_id}': {e}")
            raise TenantServiceError(f"Failed to retrieve tenant: {str(e)}")

    def get_active_tenants(self) -> List[Tenant]:
        """Get all active tenants"""
        try:
            return self.tenant_repo.get_active_tenants()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting active tenants: {e}")
            raise TenantServiceError(f"Failed to retrieve tenants: {str(e)}")

    def update_tenant_settings(self, tenant_id: UUID, settings: dict) -> Optional[Tenant]:
        """Update tenant settings"""
        try:
            tenant = self.tenant_repo.update(tenant_id, settings=settings)
            if tenant:
                self.db.commit()
                logger.info(f"Updated settings for tenant {tenant_id}")
            return tenant
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating tenant settings '{tenant_id}': {e}")
            raise TenantServiceError(f"Failed to update tenant settings: {str(e)}")

    def deactivate_tenant(self, tenant_id: UUID) -> Optional[Tenant]:
        """Deactivate a tenant and all related data"""
        try:
            tenant = self.tenant_repo.deactivate_tenant(tenant_id)
            if tenant:
                # Deactivate all users in the tenant
                users = self.user_repo.get_tenant_users(tenant_id, active_only=False)
                for user in users:
                    self.user_repo.update(user.id, is_active=False)

                self.db.commit()
                logger.info(f"Deactivated tenant {tenant_id} and {len(users)} associated users")
            return tenant
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deactivating tenant '{tenant_id}': {e}")
            raise TenantServiceError(f"Failed to deactivate tenant: {str(e)}")

    def get_tenant_users(self, tenant_id: UUID, active_only: bool = True) -> List[User]:
        """Get all users for a tenant"""
        try:
            return self.user_repo.get_tenant_users(tenant_id, active_only)
        except SQLAlchemyError as e:
            logger.error(f"Database error getting users for tenant '{tenant_id}': {e}")
            raise TenantServiceError(f"Failed to retrieve tenant users: {str(e)}")

    def add_user_to_tenant(
        self,
        tenant_id: UUID,
        telegram_user_id: str = None,
        email: str = None,
        username: str = None,
        role: UserRole = UserRole.user
    ) -> User:
        """Add a new user to a tenant"""
        try:
            # Verify tenant exists
            tenant = self.tenant_repo.get_by_id(tenant_id)
            if not tenant:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")

            user = self.user_repo.create_user(
                tenant_id=tenant_id,
                telegram_user_id=telegram_user_id,
                email=email,
                username=username,
                role=role
            )
            self.db.commit()
            logger.info(f"Added user to tenant {tenant_id} with role {role.value}")
            return user
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error adding user to tenant '{tenant_id}': {e}")
            raise UserCreationError("User with this email or telegram ID already exists")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error adding user to tenant '{tenant_id}': {e}")
            raise UserCreationError(f"Failed to add user: {str(e)}")
