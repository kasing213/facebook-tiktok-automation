# app/core/tenant.py
"""
Tenant management utilities for multi-tenant social media automation.

This module provides functions for creating, managing, and querying tenants
and their associated resources with proper data isolation.
"""
import uuid
import re
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.models import (
    Tenant, User, Destination, AdToken, Automation,
    UserRole, DestinationType, Platform
)


def create_tenant(
    db: Session,
    name: str,
    slug: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None
) -> Tenant:
    """
    Create a new tenant with proper validation.

    Args:
        db: Database session
        name: Human-readable tenant name
        slug: URL-friendly identifier (auto-generated if not provided)
        settings: Optional tenant-specific configuration

    Returns:
        Created Tenant instance

    Raises:
        ValueError: If slug is invalid or already exists
    """
    # Auto-generate slug if not provided
    if not slug:
        slug = generate_tenant_slug(name)

    # Validate slug format
    if not is_valid_slug(slug):
        raise ValueError(f"Invalid slug format: {slug}")

    # Check if slug already exists
    existing = db.query(Tenant).filter(Tenant.slug == slug).first()
    if existing:
        raise ValueError(f"Tenant with slug '{slug}' already exists")

    tenant = Tenant(
        name=name,
        slug=slug,
        settings=settings or {}
    )

    try:
        db.add(tenant)
        db.flush()  # Get the ID without committing
        return tenant
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to create tenant: {str(e)}")


def create_tenant_user(
    db: Session,
    tenant_id: str,
    telegram_user_id: Optional[str] = None,
    email: Optional[str] = None,
    username: Optional[str] = None,
    role: UserRole = UserRole.user
) -> User:
    """
    Create a new user within a tenant.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        telegram_user_id: Telegram user ID (optional)
        email: User email (optional)
        username: Display username (optional)
        role: User role within the tenant

    Returns:
        Created User instance

    Raises:
        ValueError: If user already exists or tenant not found
    """
    # Verify tenant exists
    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id,
        Tenant.is_active == True
    ).first()
    if not tenant:
        raise ValueError(f"Active tenant not found: {tenant_id}")

    # Check for existing user
    if telegram_user_id:
        existing = db.query(User).filter(
            User.tenant_id == tenant_id,
            User.telegram_user_id == telegram_user_id
        ).first()
        if existing:
            raise ValueError(f"User with Telegram ID {telegram_user_id} already exists in tenant")

    if email:
        existing = db.query(User).filter(
            User.tenant_id == tenant_id,
            User.email == email
        ).first()
        if existing:
            raise ValueError(f"User with email {email} already exists in tenant")

    user = User(
        tenant_id=tenant_id,
        telegram_user_id=telegram_user_id,
        email=email,
        username=username,
        role=role
    )

    try:
        db.add(user)
        db.flush()
        return user
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to create user: {str(e)}")


def create_telegram_destination(
    db: Session,
    tenant_id: str,
    name: str,
    chat_id: str,
    is_active: bool = True
) -> Destination:
    """
    Create a Telegram chat destination for a tenant.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        name: Human-readable name for the destination
        chat_id: Telegram chat ID
        is_active: Whether destination is active

    Returns:
        Created Destination instance
    """
    # Verify tenant exists
    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id,
        Tenant.is_active == True
    ).first()
    if not tenant:
        raise ValueError(f"Active tenant not found: {tenant_id}")

    destination = Destination(
        tenant_id=tenant_id,
        name=name,
        type=DestinationType.telegram_chat,
        config={
            "chat_id": chat_id,
            "parse_mode": "HTML"  # Default to HTML parse mode
        },
        is_active=is_active
    )

    try:
        db.add(destination)
        db.flush()
        return destination
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to create destination: {str(e)}")


def get_tenant_tokens(
    db: Session,
    tenant_id: str,
    platform: Optional[Platform] = None,
    valid_only: bool = True
) -> List[AdToken]:
    """
    Get OAuth tokens for a tenant, optionally filtered by platform.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        platform: Optional platform filter
        valid_only: Only return valid tokens

    Returns:
        List of AdToken instances
    """
    query = db.query(AdToken).filter(AdToken.tenant_id == tenant_id)

    if platform:
        query = query.filter(AdToken.platform == platform)

    if valid_only:
        query = query.filter(AdToken.is_valid == True)

    return query.order_by(AdToken.created_at.desc()).all()


def get_tenant_automations(
    db: Session,
    tenant_id: str,
    active_only: bool = True
) -> List[Automation]:
    """
    Get all automations for a tenant.

    Args:
        db: Database session
        tenant_id: Tenant UUID
        active_only: Only return active automations

    Returns:
        List of Automation instances
    """
    from app.core.models import AutomationStatus

    query = db.query(Automation).filter(Automation.tenant_id == tenant_id)

    if active_only:
        query = query.filter(Automation.status == AutomationStatus.active)

    return query.order_by(Automation.created_at.desc()).all()


def get_tenant_stats(db: Session, tenant_id: str) -> Dict[str, Any]:
    """
    Get usage statistics for a tenant.

    Args:
        db: Database session
        tenant_id: Tenant UUID

    Returns:
        Dictionary with tenant statistics
    """
    from app.core.models import AutomationStatus

    # Count various resources
    user_count = db.query(User).filter(
        User.tenant_id == tenant_id,
        User.is_active == True
    ).count()

    destination_count = db.query(Destination).filter(
        Destination.tenant_id == tenant_id,
        Destination.is_active == True
    ).count()

    token_count = db.query(AdToken).filter(
        AdToken.tenant_id == tenant_id,
        AdToken.is_valid == True
    ).count()

    active_automation_count = db.query(Automation).filter(
        Automation.tenant_id == tenant_id,
        Automation.status == AutomationStatus.active
    ).count()

    total_automation_count = db.query(Automation).filter(
        Automation.tenant_id == tenant_id
    ).count()

    # Platform breakdown
    platform_tokens = db.query(AdToken.platform, db.func.count()).filter(
        AdToken.tenant_id == tenant_id,
        AdToken.is_valid == True
    ).group_by(AdToken.platform).all()

    return {
        "users": user_count,
        "destinations": destination_count,
        "valid_tokens": token_count,
        "active_automations": active_automation_count,
        "total_automations": total_automation_count,
        "platforms": dict(platform_tokens)
    }


def deactivate_tenant(db: Session, tenant_id: str) -> bool:
    """
    Deactivate a tenant and all associated resources.

    Args:
        db: Database session
        tenant_id: Tenant UUID

    Returns:
        True if tenant was deactivated, False if not found
    """
    from app.core.models import AutomationStatus

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return False

    # Deactivate tenant
    tenant.is_active = False

    # Deactivate all users
    db.query(User).filter(User.tenant_id == tenant_id).update({"is_active": False})

    # Deactivate all destinations
    db.query(Destination).filter(Destination.tenant_id == tenant_id).update({"is_active": False})

    # Stop all automations
    db.query(Automation).filter(Automation.tenant_id == tenant_id).update({"status": AutomationStatus.stopped})

    # Mark tokens as invalid
    db.query(AdToken).filter(AdToken.tenant_id == tenant_id).update({"is_valid": False})

    try:
        db.flush()
        return True
    except IntegrityError:
        db.rollback()
        return False


# Utility functions
def generate_tenant_slug(name: str) -> str:
    """
    Generate a URL-friendly slug from tenant name.

    Args:
        name: Tenant name

    Returns:
        Generated slug
    """
    # Convert to lowercase, replace spaces and special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')

    # Add random suffix to ensure uniqueness
    suffix = str(uuid.uuid4())[:8]
    return f"{slug}-{suffix}"


def is_valid_slug(slug: str) -> bool:
    """
    Validate slug format.

    Args:
        slug: Slug to validate

    Returns:
        True if valid, False otherwise
    """
    if not slug or len(slug) < 3 or len(slug) > 100:
        return False

    # Only allow alphanumeric characters and hyphens
    pattern = r'^[a-z0-9-]+$'
    return bool(re.match(pattern, slug))


def get_tenant_context(db: Session, tenant_id: str) -> Optional[Dict[str, Any]]:
    """
    Get complete tenant context including basic info and relationships.

    Args:
        db: Database session
        tenant_id: Tenant UUID

    Returns:
        Tenant context dictionary or None if not found
    """
    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id,
        Tenant.is_active == True
    ).first()

    if not tenant:
        return None

    stats = get_tenant_stats(db, tenant_id)

    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "settings": tenant.settings,
        "created_at": tenant.created_at.isoformat(),
        "stats": stats
    }