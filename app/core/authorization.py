# app/core/authorization.py
"""
Role-based authorization decorators and utilities.
"""
from functools import wraps
from typing import Callable, List, Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import User, UserRole
from app.core.dependencies import get_current_user


class InsufficientPermissions(HTTPException):
    """Raised when user lacks required permissions"""
    def __init__(self, required_role: str, user_role: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This operation requires '{required_role}' role. Your role: '{user_role}'"
        )


class TenantOwnerRequired(HTTPException):
    """Raised when operation requires tenant owner"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation is restricted to tenant owners only"
        )


def require_role(*allowed_roles: UserRole):
    """
    Decorator to enforce role-based access control.

    Usage:
        @require_role(UserRole.admin, UserRole.owner)
        async def admin_only_endpoint():
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from the function's dependencies
            current_user = None

            # Look for current_user in kwargs (from Depends)
            if 'current_user' in kwargs:
                current_user = kwargs['current_user']
            else:
                # Fallback: look in args for User instance
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            if current_user.role not in allowed_roles:
                raise InsufficientPermissions(
                    required_role=" or ".join([role.value for role in allowed_roles]),
                    user_role=current_user.role.value
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_owner(func: Callable):
    """
    Decorator to require tenant owner role.
    Equivalent to @require_role(UserRole.admin) but with clearer error message.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get current user from the function's dependencies
        current_user = None

        # Look for current_user in kwargs (from Depends)
        if 'current_user' in kwargs:
            current_user = kwargs['current_user']
        else:
            # Fallback: look in args for User instance
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break

        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        if current_user.role != UserRole.admin:
            raise TenantOwnerRequired()

        return await func(*args, **kwargs)
    return wrapper


async def get_current_owner(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current user and enforce owner role.

    Usage:
        async def owner_endpoint(owner: User = Depends(get_current_owner)):
            # owner is guaranteed to have UserRole.admin
    """
    if current_user.role != UserRole.admin:
        raise TenantOwnerRequired()

    return current_user


async def get_current_member_or_owner(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current user and enforce member or owner role.
    Excludes viewer role.
    """
    if current_user.role not in [UserRole.admin, UserRole.user]:
        raise InsufficientPermissions(
            required_role="member or owner",
            user_role=current_user.role.value
        )

    return current_user


def check_subscription_feature(feature_name: str, user: User, db: Session) -> bool:
    """
    Check if user's tenant subscription allows access to a feature.

    Access Rules:
    - Owner (admin role): FULL ACCESS always, regardless of subscription
    - Member (user role): FULL ACCESS only if tenant has Pro subscription
    - Viewer role: Restricted to view-only features

    Subscription Limits:
    - Free: 1 user (owner only)
    - Pro ($10/month): 2 users (owner + 1 member)

    Args:
        feature_name: Name of the feature to check
        user: Current user
        db: Database session

    Returns:
        True if feature is allowed, False otherwise
    """
    from app.core.models import SubscriptionTier, Subscription

    # Rule 1: Owner (admin role) ALWAYS has full access
    if user.role == UserRole.admin:
        return True

    # Rule 2: For members, check tenant's subscription via owner
    # Find the owner's subscription for this tenant
    owner_subscription = db.query(Subscription).join(User).filter(
        User.tenant_id == user.tenant_id,
        User.role == UserRole.admin
    ).first()

    # Check subscription tier and feature access
    subscription_tier = owner_subscription.tier if owner_subscription else SubscriptionTier.free

    # Define features by subscription tier
    free_features = {
        'invoice_create',
        'invoice_view',
        'invoice_send',
        'payment_verify',
        'telegram_link',
        'basic_reports'
    }

    invoice_plus_features = free_features | {
        'bulk_operations',    # Export invoices
        'advanced_inventory', # Product management
        'customer_management',
    }

    marketing_plus_features = free_features | {
        'social_automation',  # Facebook/TikTok
        'ads_alerts',        # Promotions/broadcasts
        'promotion_create',
        'promotion_send',
    }

    pro_features = invoice_plus_features | marketing_plus_features  # All features

    # Check feature access based on subscription
    if subscription_tier == SubscriptionTier.pro:
        return feature_name in pro_features
    elif subscription_tier == SubscriptionTier.invoice_plus:
        return feature_name in invoice_plus_features
    elif subscription_tier == SubscriptionTier.marketing_plus:
        return feature_name in marketing_plus_features
    else:
        # Free tier - basic features only
        return feature_name in free_features


def require_subscription_feature(feature_name: str):
    """
    Decorator to enforce subscription-based feature access.

    Usage:
        @require_subscription_feature('advanced_reports')
        async def advanced_reports_endpoint():
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = None
            db = None

            # Find current_user and db in kwargs
            if 'current_user' in kwargs:
                current_user = kwargs['current_user']
            if 'db' in kwargs:
                db = kwargs['db']

            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing user or database context for subscription check"
                )

            if not check_subscription_feature(feature_name, current_user, db):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Feature '{feature_name}' requires Pro subscription. Upgrade your plan to continue."
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator