"""Usage limits and fair usage policy enforcement"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.models import Tenant, SubscriptionTier


class UsageLimitExceeded(HTTPException):
    """Raised when tenant hits usage limit - returns 402 Payment Required"""

    def __init__(
        self,
        resource: str,
        current: int,
        limit: int,
        upgrade_url: str = "/subscription/upgrade"
    ):
        detail = {
            "error": f"{resource}_limit_reached",
            "message": f"You've reached your {resource} limit ({current}/{limit})",
            "current": current,
            "limit": limit,
            "upgrade_url": upgrade_url,
            "resets_at": get_next_reset_date().isoformat() if resource in ['invoice', 'export'] else None
        }
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail
        )


def get_next_reset_date() -> datetime:
    """Get next month's first day at midnight UTC for monthly limit reset"""
    now = datetime.now(timezone.utc)
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return next_month


def get_tenant_usage_limits(tenant_id: UUID, db: Session) -> Dict:
    """Get current usage limits and counters for tenant"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get subscription tier to determine if limits apply
    subscription_tier = getattr(tenant, 'subscription_tier', SubscriptionTier.free)

    return {
        "limits": {
            "invoice": tenant.invoice_limit,
            "product": tenant.product_limit,
            "customer": tenant.customer_limit,
            "team_member": tenant.team_member_limit,
            "storage_mb": tenant.storage_limit_mb,
            "api_calls_hourly": tenant.api_calls_limit_hourly,
            "promotion": tenant.promotion_limit,
            "broadcast_recipients": tenant.broadcast_recipient_limit
        },
        "current_usage": {
            "invoices": tenant.current_month_invoices,
            "exports": tenant.current_month_exports,
            "promotions": tenant.current_month_promotions,
            "broadcasts": tenant.current_month_broadcasts,
            "storage_mb": float(tenant.storage_used_mb) if tenant.storage_used_mb else 0.0
        },
        "subscription_tier": subscription_tier,
        "reset_date": tenant.current_month_reset_at.isoformat() if tenant.current_month_reset_at else None,
        "unlimited": subscription_tier == SubscriptionTier.pro
    }


async def check_invoice_limit(tenant_id: UUID, db: Session) -> None:
    """Check if tenant can create another invoice"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Invoice Plus and Pro tiers have higher limits
    subscription_tier = getattr(tenant, 'subscription_tier', SubscriptionTier.free)
    if subscription_tier in [SubscriptionTier.invoice_plus, SubscriptionTier.pro]:
        # High limit for paid tiers (effectively unlimited)
        if tenant.current_month_invoices >= 200:
            raise UsageLimitExceeded(
                resource="invoice",
                current=tenant.current_month_invoices,
                limit=200
            )
        return

    # Free tier: reduced limit
    free_limit = 20  # Reduced from 50 to encourage upgrade
    if tenant.current_month_invoices >= free_limit:
        raise UsageLimitExceeded(
            resource="invoice",
            current=tenant.current_month_invoices,
            limit=free_limit
        )


async def check_customer_limit(tenant_id: UUID, db: Session) -> None:
    """Check if tenant can create another customer"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Set limits based on subscription tier
    subscription_tier = getattr(tenant, 'subscription_tier', SubscriptionTier.free)
    if subscription_tier in [SubscriptionTier.invoice_plus, SubscriptionTier.pro]:
        limit = 250  # Paid tiers get higher limit
    else:
        limit = 25   # Free tier reduced limit

    # Count current customers
    result = db.execute(text("""
        SELECT COUNT(*) as count
        FROM invoice.customer
        WHERE tenant_id = :tenant_id
    """), {"tenant_id": tenant_id})

    current_count = result.fetchone().count

    if current_count >= limit:
        raise UsageLimitExceeded(
            resource="customer",
            current=current_count,
            limit=limit
        )


async def check_product_limit(tenant_id: UUID, db: Session) -> None:
    """Check if tenant can create another product"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Set limits based on subscription tier
    subscription_tier = getattr(tenant, 'subscription_tier', SubscriptionTier.free)
    if subscription_tier in [SubscriptionTier.invoice_plus, SubscriptionTier.pro]:
        limit = 500  # Paid tiers get higher limit
    else:
        limit = 50   # Free tier reduced limit

    # Count current active products
    result = db.execute(text("""
        SELECT COUNT(*) as count
        FROM inventory.products
        WHERE tenant_id = :tenant_id AND is_active = true
    """), {"tenant_id": tenant_id})

    current_count = result.fetchone().count

    if current_count >= limit:
        raise UsageLimitExceeded(
            resource="product",
            current=current_count,
            limit=limit
        )


async def check_team_member_limit(tenant_id: UUID, db: Session) -> None:
    """
    Check if tenant can add another team member.

    Limits:
    - Free tier: 1 user (owner only)
    - Pro tier: 2 users (owner + 1 member)
    """
    from app.core.models import Subscription, User, UserRole

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Check owner's subscription to determine tier
    owner_subscription = db.query(Subscription).join(User).filter(
        User.tenant_id == tenant_id,
        User.role == UserRole.admin
    ).first()

    # Set limit based on subscription: Pro = 2, Free = 1
    if owner_subscription and owner_subscription.tier == SubscriptionTier.pro:
        limit = 2  # Owner + 1 member
    else:
        limit = 1  # Owner only

    # Count current active users
    result = db.execute(text("""
        SELECT COUNT(*) as count
        FROM "user"
        WHERE tenant_id = :tenant_id AND is_active = true
    """), {"tenant_id": tenant_id})

    current_count = result.fetchone().count

    if current_count >= limit:
        raise UsageLimitExceeded(
            resource="team_member",
            current=current_count,
            limit=limit
        )


async def check_export_limit(tenant_id: UUID, db: Session) -> None:
    """Check if tenant can export (PDF/XLSX)"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Set limits based on subscription tier
    subscription_tier = getattr(tenant, 'subscription_tier', SubscriptionTier.free)
    if subscription_tier in [SubscriptionTier.invoice_plus, SubscriptionTier.pro]:
        export_limit = 100  # Paid tiers get higher limit
    else:
        export_limit = 10   # Free tier reduced limit

    if tenant.current_month_exports >= export_limit:
        raise UsageLimitExceeded(
            resource="export",
            current=tenant.current_month_exports,
            limit=export_limit
        )


def increment_invoice_counter(tenant_id: UUID, db: Session) -> None:
    """Increment monthly invoice counter after successful creation"""
    db.execute(text("""
        UPDATE tenant
        SET current_month_invoices = current_month_invoices + 1
        WHERE id = :tenant_id
    """), {"tenant_id": tenant_id})
    db.commit()


def increment_export_counter(tenant_id: UUID, db: Session) -> None:
    """Increment monthly export counter after successful export"""
    db.execute(text("""
        UPDATE tenant
        SET current_month_exports = current_month_exports + 1
        WHERE id = :tenant_id
    """), {"tenant_id": tenant_id})
    db.commit()


async def check_promotion_limit(tenant_id: UUID, db: Session) -> None:
    """Check if tenant can create another promotion (anti-abuse for Telegram)"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Free tier: NO promotions allowed (prevent spam)
    subscription_tier = getattr(tenant, 'subscription_tier', SubscriptionTier.free)
    if subscription_tier == SubscriptionTier.free:
        raise UsageLimitExceeded(
            resource="promotion",
            current=tenant.current_month_promotions,
            limit=0
        )

    # Set limits based on subscription tier
    if subscription_tier == SubscriptionTier.marketing_plus:
        promotion_limit = 10
    elif subscription_tier == SubscriptionTier.pro:
        promotion_limit = 20  # Double limit for combined subscription
    else:
        promotion_limit = 0   # Invoice Plus doesn't include marketing

    if tenant.current_month_promotions >= promotion_limit:
        raise UsageLimitExceeded(
            resource="promotion",
            current=tenant.current_month_promotions,
            limit=promotion_limit
        )


async def check_broadcast_limit(tenant_id: UUID, recipient_count: int, db: Session) -> None:
    """Check if tenant can broadcast to this many recipients (anti-abuse)"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Free tier: NO broadcasts allowed (prevent spam)
    subscription_tier = getattr(tenant, 'subscription_tier', SubscriptionTier.free)
    if subscription_tier == SubscriptionTier.free:
        raise UsageLimitExceeded(
            resource="broadcast",
            current=tenant.current_month_broadcasts,
            limit=0
        )

    # Set monthly recipient limits
    if subscription_tier == SubscriptionTier.marketing_plus:
        broadcast_limit = 500
    elif subscription_tier == SubscriptionTier.pro:
        broadcast_limit = 1000  # Double limit for combined subscription
    else:
        broadcast_limit = 0     # Invoice Plus doesn't include marketing

    # Check if this broadcast would exceed monthly limit
    new_total = tenant.current_month_broadcasts + recipient_count
    if new_total > broadcast_limit:
        raise UsageLimitExceeded(
            resource="broadcast",
            current=tenant.current_month_broadcasts,
            limit=broadcast_limit
        )


def increment_promotion_counter(tenant_id: UUID, db: Session) -> None:
    """Increment monthly promotion counter after successful creation"""
    db.execute(text("""
        UPDATE tenant
        SET current_month_promotions = current_month_promotions + 1
        WHERE id = :tenant_id
    """), {"tenant_id": tenant_id})
    db.commit()


def increment_broadcast_counter(tenant_id: UUID, recipient_count: int, db: Session) -> None:
    """Increment monthly broadcast counter after successful send"""
    db.execute(text("""
        UPDATE tenant
        SET current_month_broadcasts = current_month_broadcasts + :count
        WHERE id = :tenant_id
    """), {"tenant_id": tenant_id, "count": recipient_count})
    db.commit()


async def check_and_notify_usage_warnings(tenant_id: UUID, db: Session) -> Optional[Dict]:
    """Check usage levels and return warning if approaching limits (80%+)"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return None

    warnings = []

    # Check invoice usage (80% threshold)
    invoice_percentage = (tenant.current_month_invoices / tenant.invoice_limit) * 100
    if invoice_percentage >= 80:
        warnings.append({
            "type": "invoice",
            "percentage": int(invoice_percentage),
            "current": tenant.current_month_invoices,
            "limit": tenant.invoice_limit,
            "message": f"You've used {tenant.current_month_invoices}/{tenant.invoice_limit} invoices this month ({int(invoice_percentage)}%)"
        })

    # Check export usage (80% threshold)
    export_limit = 20  # Free tier limit
    export_percentage = (tenant.current_month_exports / export_limit) * 100
    if export_percentage >= 80:
        warnings.append({
            "type": "export",
            "percentage": int(export_percentage),
            "current": tenant.current_month_exports,
            "limit": export_limit,
            "message": f"You've used {tenant.current_month_exports}/{export_limit} exports this month ({int(export_percentage)}%)"
        })

    if warnings:
        return {
            "warnings": warnings,
            "upgrade_url": "/subscription/upgrade",
            "resets_at": get_next_reset_date().isoformat()
        }

    return None


def update_subscription_limits(tenant_id: UUID, tier: SubscriptionTier, db: Session) -> None:
    """Update tenant limits when subscription tier changes"""
    if tier == SubscriptionTier.invoice_plus:
        # Invoice Plus: $10/month - Invoice + Inventory features
        limits = {
            "invoice_limit": 200,
            "product_limit": 500,
            "customer_limit": 250,
            "team_member_limit": 2,  # Owner + 1 member
            "storage_limit_mb": 1024,  # 1 GB
            "api_calls_limit_hourly": 200,
            "promotion_limit": 0,      # No marketing features
            "broadcast_recipient_limit": 0
        }
    elif tier == SubscriptionTier.marketing_plus:
        # Marketing Plus: $10/month - Social + Ads Alerts features
        limits = {
            "invoice_limit": 20,       # Basic invoice (same as free)
            "product_limit": 50,       # Basic inventory (same as free)
            "customer_limit": 25,      # Basic customers (same as free)
            "team_member_limit": 2,    # Owner + 1 member
            "storage_limit_mb": 512,   # 500 MB
            "api_calls_limit_hourly": 200,
            "promotion_limit": 10,     # Marketing features
            "broadcast_recipient_limit": 500
        }
    elif tier == SubscriptionTier.pro:
        # Pro: $20/month - Both products combined
        limits = {
            "invoice_limit": 200,
            "product_limit": 500,
            "customer_limit": 250,
            "team_member_limit": 3,    # Owner + 2 members
            "storage_limit_mb": 2048,  # 2 GB
            "api_calls_limit_hourly": 500,
            "promotion_limit": 20,     # Double marketing limit
            "broadcast_recipient_limit": 1000
        }
    else:
        # Free tier limits (very restricted to encourage upgrades)
        limits = {
            "invoice_limit": 20,       # Reduced from 50
            "product_limit": 50,       # Reduced from 100
            "customer_limit": 25,      # Reduced from 50
            "team_member_limit": 1,    # Owner only
            "storage_limit_mb": 100,   # Reduced from 500
            "api_calls_limit_hourly": 50,  # Reduced from 100
            "promotion_limit": 0,      # No marketing features
            "broadcast_recipient_limit": 0
        }

    db.execute(text("""
        UPDATE tenant
        SET invoice_limit = :invoice_limit,
            product_limit = :product_limit,
            customer_limit = :customer_limit,
            team_member_limit = :team_member_limit,
            storage_limit_mb = :storage_limit_mb,
            api_calls_limit_hourly = :api_calls_limit_hourly,
            promotion_limit = :promotion_limit,
            broadcast_recipient_limit = :broadcast_recipient_limit
        WHERE id = :tenant_id
    """), {**limits, "tenant_id": tenant_id})
    db.commit()