# app/repositories/user.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.models import User, UserRole
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user operations"""

    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_telegram_id(self, tenant_id: UUID, telegram_user_id: str) -> Optional[User]:
        """Get user by tenant and Telegram ID"""
        return self.find_one_by(tenant_id=tenant_id, telegram_user_id=telegram_user_id)

    def get_by_email(self, tenant_id: UUID, email: str) -> Optional[User]:
        """Get user by tenant and email"""
        return self.find_one_by(tenant_id=tenant_id, email=email)

    def get_tenant_users(self, tenant_id: UUID, active_only: bool = True) -> List[User]:
        """Get all users for a tenant"""
        filters = {"tenant_id": tenant_id}
        if active_only:
            filters["is_active"] = True
        return self.find_by(**filters)

    def get_by_username(self, tenant_id: UUID, username: str) -> Optional[User]:
        """Get user by tenant and username"""
        return self.find_one_by(tenant_id=tenant_id, username=username)

    def get_by_username_global(self, username: str) -> Optional[User]:
        """Get user by username across all tenants (for login)"""
        return self.db.query(User).filter(User.username == username).first()

    def create_user(
        self,
        tenant_id: UUID,
        telegram_user_id: str = None,
        email: str = None,
        username: str = None,
        password_hash: str = None,
        email_verified: bool = False,
        role: UserRole = UserRole.user
    ) -> User:
        """Create a new user with validation"""
        if telegram_user_id and self.get_by_telegram_id(tenant_id, telegram_user_id):
            raise ValueError(f"User with Telegram ID '{telegram_user_id}' already exists in this tenant")

        if email and self.get_by_email(tenant_id, email):
            raise ValueError(f"User with email '{email}' already exists in this tenant")

        if username and self.get_by_username(tenant_id, username):
            raise ValueError(f"User with username '{username}' already exists in this tenant")

        return self.create(
            tenant_id=tenant_id,
            telegram_user_id=telegram_user_id,
            email=email,
            username=username,
            password_hash=password_hash,
            email_verified=email_verified,
            role=role,
            is_active=True
        )

    def update_last_login(self, user_id: UUID) -> Optional[User]:
        """Update user's last login timestamp"""
        from datetime import datetime
        return self.update(user_id, last_login=datetime.utcnow())

    def get_admins(self, tenant_id: UUID) -> List[User]:
        """Get all admin users for a tenant"""
        return self.find_by(tenant_id=tenant_id, role=UserRole.admin, is_active=True)

    def update_password(self, user_id: UUID, password_hash: str) -> Optional[User]:
        """Update user's password hash"""
        return self.update(user_id, password_hash=password_hash)

    def count_tenant_users(self, tenant_id: UUID, active_only: bool = True) -> int:
        """Count users in a tenant"""
        query = self.db.query(User).filter(User.tenant_id == tenant_id)
        if active_only:
            query = query.filter(User.is_active == True)
        return query.count()

    def is_first_user_in_tenant(self, tenant_id: UUID) -> bool:
        """Check if this would be the first user in the tenant"""
        return self.count_tenant_users(tenant_id, active_only=True) == 0