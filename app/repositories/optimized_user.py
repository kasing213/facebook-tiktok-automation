# app/repositories/optimized_user.py
"""
Optimized user repository with caching and reduced database pressure.

Demonstrates best practices for:
- Query result caching
- Bulk operations
- Connection efficiency
- Performance monitoring
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.core.models import User, UserRole
from app.core.cache import cached, cache_user_data, invalidate_user_cache
from app.repositories.optimized_base import TenantAwareRepository

class OptimizedUserRepository(TenantAwareRepository[User]):
    """Optimized user repository with caching and bulk operations"""

    def __init__(self, db: Session):
        super().__init__(db, User)

    # Cached lookups for frequently accessed data
    @cache_user_data
    def get_by_telegram_id(self, tenant_id: UUID, telegram_user_id: str) -> Optional[User]:
        """Get user by tenant and Telegram ID with caching"""
        return self.db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.telegram_user_id == telegram_user_id,
                User.is_active == True
            )
        ).first()

    @cache_user_data
    def get_by_email(self, tenant_id: UUID, email: str) -> Optional[User]:
        """Get user by tenant and email with caching"""
        return self.db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.email == email,
                User.is_active == True
            )
        ).first()

    @cache_user_data
    def get_by_username(self, tenant_id: UUID, username: str) -> Optional[User]:
        """Get user by tenant and username with caching"""
        return self.db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.username == username,
                User.is_active == True
            )
        ).first()

    # Global lookups (for authentication) - shorter cache TTL
    @cached(ttl=300, key_prefix="user_by_username_global")
    def get_by_username_global(self, username: str) -> Optional[User]:
        """Get user by username across all tenants (for login) with caching"""
        return self.db.query(User).filter(
            and_(User.username == username, User.is_active == True)
        ).first()

    @cached(ttl=300, key_prefix="user_by_email_global")
    def get_by_email_global(self, email: str) -> Optional[User]:
        """Get user by email across all tenants (for password reset) with caching"""
        return self.db.query(User).filter(
            and_(User.email == email, User.is_active == True)
        ).first()

    # Optimized tenant user operations
    def get_tenant_users_paginated(
        self,
        tenant_id: UUID,
        page: int = 1,
        limit: int = 50,
        role: UserRole = None,
        active_only: bool = True,
        search: str = None
    ) -> Dict[str, Any]:
        """Get paginated tenant users with search and filtering"""
        query = self.db.query(User).filter(User.tenant_id == tenant_id)

        # Apply filters
        if active_only:
            query = query.filter(User.is_active == True)

        if role:
            query = query.filter(User.role == role)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                and_(
                    User.username.ilike(search_term) |
                    User.email.ilike(search_term)
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        users = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

        return {
            'users': users,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }

    # Bulk user operations for efficiency
    def bulk_create_users(self, tenant_id: UUID, user_data_list: List[Dict[str, Any]]) -> List[User]:
        """
        Efficiently create multiple users in a single transaction.
        Reduces database round-trips.
        """
        if not user_data_list:
            return []

        # Add tenant_id and defaults to each user
        for user_data in user_data_list:
            user_data['tenant_id'] = tenant_id
            user_data.setdefault('is_active', True)
            user_data.setdefault('role', UserRole.user)
            user_data.setdefault('email_verified', False)

        # Use parent class bulk create
        users = self.bulk_create(user_data_list)

        # Invalidate relevant caches
        invalidate_user_cache(str(tenant_id))

        return users

    def bulk_update_last_login(self, user_ids: List[UUID], login_time: datetime = None) -> int:
        """Bulk update last login timestamps"""
        if not user_ids:
            return 0

        login_time = login_time or datetime.utcnow()

        result = self.db.query(User).filter(
            User.id.in_(user_ids)
        ).update({User.last_login: login_time}, synchronize_session=False)

        self.db.flush()
        return result

    # Cached aggregations and statistics
    @cached(ttl=600, key_prefix="user_stats")
    def get_tenant_user_stats(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get comprehensive user statistics for a tenant"""
        base_query = self.db.query(User).filter(User.tenant_id == tenant_id)

        # Get counts by status
        total_users = base_query.count()
        active_users = base_query.filter(User.is_active == True).count()
        inactive_users = total_users - active_users

        # Get counts by role
        role_counts = {}
        for role in UserRole:
            count = base_query.filter(
                and_(User.role == role, User.is_active == True)
            ).count()
            role_counts[role.value] = count

        # Get recent activity
        recent_threshold = datetime.utcnow() - timedelta(days=7)
        recent_logins = base_query.filter(
            and_(
                User.last_login >= recent_threshold,
                User.is_active == True
            )
        ).count()

        # Get verified email count
        verified_emails = base_query.filter(
            and_(
                User.email_verified == True,
                User.is_active == True,
                User.email.isnot(None)
            )
        ).count()

        return {
            'tenant_id': str(tenant_id),
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'role_distribution': role_counts,
            'recent_logins_7d': recent_logins,
            'verified_emails': verified_emails,
            'last_updated': datetime.utcnow().isoformat()
        }

    @cached(ttl=300, key_prefix="admins")
    def get_tenant_admins(self, tenant_id: UUID) -> List[User]:
        """Get admin users for tenant with caching"""
        return self.db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.role == UserRole.admin,
                User.is_active == True
            )
        ).all()

    # User validation with caching
    @cached(ttl=60, key_prefix="user_exists")
    def check_username_exists(self, tenant_id: UUID, username: str, exclude_user_id: UUID = None) -> bool:
        """Check if username exists in tenant (cached for form validation)"""
        query = self.db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.username == username,
                User.is_active == True
            )
        )

        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)

        return query.first() is not None

    @cached(ttl=60, key_prefix="email_exists")
    def check_email_exists(self, tenant_id: UUID, email: str, exclude_user_id: UUID = None) -> bool:
        """Check if email exists in tenant (cached for form validation)"""
        query = self.db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.email == email,
                User.is_active == True
            )
        )

        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)

        return query.first() is not None

    # Optimized user creation with validation
    def create_user_optimized(
        self,
        tenant_id: UUID,
        telegram_user_id: str = None,
        email: str = None,
        username: str = None,
        password_hash: str = None,
        email_verified: bool = False,
        role: UserRole = UserRole.user
    ) -> User:
        """
        Create user with optimized validation and cache management.
        Reduces database round-trips through bulk validation.
        """
        # Batch validation queries
        existing_checks = []

        if telegram_user_id:
            existing_checks.append(('telegram_user_id', telegram_user_id))
        if email:
            existing_checks.append(('email', email))
        if username:
            existing_checks.append(('username', username))

        if existing_checks:
            # Single query to check all potential conflicts
            conditions = []
            for field, value in existing_checks:
                conditions.append(getattr(User, field) == value)

            existing_user = self.db.query(User).filter(
                and_(
                    User.tenant_id == tenant_id,
                    User.is_active == True,
                    and_(*conditions) if len(conditions) > 1 else conditions[0]
                )
            ).first()

            if existing_user:
                # Determine which field conflicts
                for field, value in existing_checks:
                    if getattr(existing_user, field) == value:
                        raise ValueError(f"User with {field} '{value}' already exists in this tenant")

        # Create user
        user = self.create(
            tenant_id=tenant_id,
            telegram_user_id=telegram_user_id,
            email=email,
            username=username,
            password_hash=password_hash,
            email_verified=email_verified,
            role=role
        )

        # Invalidate relevant caches
        invalidate_user_cache(str(tenant_id))

        return user

    # Advanced querying methods
    def get_users_by_activity(
        self,
        tenant_id: UUID,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get users sorted by recent activity"""
        threshold_date = datetime.utcnow() - timedelta(days=days)

        users = self.db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.is_active == True,
                User.last_login.isnot(None)
            )
        ).order_by(User.last_login.desc()).limit(limit).all()

        return [
            {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'role': user.role.value,
                'days_since_login': (datetime.utcnow() - user.last_login).days if user.last_login else None
            }
            for user in users
        ]

    def cleanup_inactive_users(self, tenant_id: UUID, inactive_days: int = 90) -> int:
        """Soft delete users inactive for specified days"""
        threshold_date = datetime.utcnow() - timedelta(days=inactive_days)

        result = self.db.query(User).filter(
            and_(
                User.tenant_id == tenant_id,
                User.is_active == True,
                User.last_login < threshold_date,
                User.role != UserRole.owner  # Never auto-deactivate owners
            )
        ).update({User.is_active: False}, synchronize_session=False)

        if result > 0:
            invalidate_user_cache(str(tenant_id))

        return result