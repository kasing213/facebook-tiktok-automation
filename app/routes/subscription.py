# app/routes/subscription.py
"""
Subscription management routes for tenant owners.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import User, SubscriptionTier, SubscriptionStatus
from app.core.authorization import get_current_owner
from app.repositories import UserRepository


router = APIRouter(prefix="/subscription", tags=["subscription"])


# Request/Response Models
class SubscriptionInfo(BaseModel):
    """Subscription information response"""
    tier: SubscriptionTier
    status: Optional[SubscriptionStatus]
    current_period_start: Optional[str]
    current_period_end: Optional[str]
    cancel_at_period_end: bool
    stripe_customer_id: Optional[str]
    features: dict


class ChangePlanRequest(BaseModel):
    """Change subscription plan request"""
    new_tier: SubscriptionTier
    billing_cycle: str = "monthly"  # monthly, yearly


# Routes
@router.get("/", response_model=SubscriptionInfo)
async def get_subscription_info(
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Get current subscription information (owner only).

    Args:
        owner: Current tenant owner
        db: Database session

    Returns:
        Subscription details and available features
    """
    # Get user's subscription (direct relationship: User -> Subscription)
    subscription = None
    if hasattr(owner, 'subscription') and owner.subscription:
        subscription = owner.subscription
    else:
        # Fallback: query database directly
        from app.core.models import Subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == owner.id
        ).first()

    # Default to free tier if no subscription
    tier = subscription.tier if subscription else SubscriptionTier.free
    status = subscription.status if subscription else None

    # Define features based on tier
    features = {
        "invoice_create": True,
        "invoice_send": True,
        "invoice_view": True,
        "payment_verify": True,
        "telegram_link": True,
        "basic_reports": True,
        "advanced_reports": tier == SubscriptionTier.pro,
        "bulk_operations": tier == SubscriptionTier.pro,
        "custom_branding": tier == SubscriptionTier.pro,
        "api_access": tier == SubscriptionTier.pro,
        "priority_support": tier == SubscriptionTier.pro,
        "unlimited_invoices": tier == SubscriptionTier.pro,
        "team_collaboration": tier == SubscriptionTier.pro
    }

    return SubscriptionInfo(
        tier=tier,
        status=status,
        current_period_start=subscription.current_period_start.isoformat() if subscription and subscription.current_period_start else None,
        current_period_end=subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
        cancel_at_period_end=subscription.cancel_at_period_end if subscription else False,
        stripe_customer_id=subscription.stripe_customer_id if subscription else None,
        features=features
    )


@router.post("/change")
async def change_subscription_plan(
    change_request: ChangePlanRequest,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Change subscription plan (owner only).
    Uses local bank transfer + OCR verification instead of Stripe.

    Args:
        change_request: New plan details
        owner: Current tenant owner
        db: Database session

    Returns:
        Redirect to payment instructions or change result
    """
    # Get user's subscription (direct relationship: User -> Subscription)
    current_subscription = None
    if hasattr(owner, 'subscription') and owner.subscription:
        current_subscription = owner.subscription
    else:
        current_subscription = db.query(Subscription).filter(
            Subscription.user_id == owner.id
        ).first()

    current_tier = current_subscription.tier if current_subscription else SubscriptionTier.free

    # Handle downgrades
    if change_request.new_tier == SubscriptionTier.free and current_tier == SubscriptionTier.pro:
        # Check if tenant is using pro features that would be lost
        user_repo = UserRepository(db)
        user_count = user_repo.count_tenant_users(owner.tenant_id)

        # Free tier limit: 3 users max
        if user_count > 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot downgrade to Free plan. You have {user_count} users but Free plan allows maximum 3 users. Remove users first."
            )

        # Process downgrade immediately (no payment required)
        from sqlalchemy import text
        await downgrade_tenant_subscription(owner.tenant_id, db)

        return {
            "success": True,
            "message": "Subscription downgraded to Free plan",
            "current_tier": "free",
            "new_tier": change_request.new_tier.value,
            "requires_payment": False
        }

    # Handle upgrades (require payment)
    if change_request.new_tier == SubscriptionTier.pro and current_tier == SubscriptionTier.free:
        return {
            "success": True,
            "message": "Upgrade to Pro requires payment verification",
            "current_tier": current_tier.value,
            "new_tier": change_request.new_tier.value,
            "requires_payment": True,
            "next_step": "Use /subscription-payment/upgrade-request to generate payment instructions",
            "billing_cycle": change_request.billing_cycle
        }

    # No change needed
    if change_request.new_tier == current_tier:
        return {
            "success": True,
            "message": f"Already subscribed to {current_tier.value} plan",
            "current_tier": current_tier.value,
            "new_tier": change_request.new_tier.value,
            "requires_payment": False
        }


async def downgrade_tenant_subscription(tenant_id, db):
    """Downgrade tenant to free tier"""
    from sqlalchemy import text

    db.execute(text("""
        UPDATE subscription
        SET tier = 'free', status = 'active',
            updated_at = NOW()
        WHERE tenant_id = :tenant_id
    """), {"tenant_id": str(tenant_id)})
    db.commit()


@router.post("/cancel")
async def cancel_subscription(
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Cancel subscription at end of billing period (owner only).

    Args:
        owner: Current tenant owner
        db: Database session

    Returns:
        Cancellation result
    """
    # Get user's subscription (direct relationship: User -> Subscription)
    subscription = None
    if hasattr(owner, 'subscription') and owner.subscription:
        subscription = owner.subscription
    else:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == owner.id
        ).first()

    if not subscription or subscription.tier == SubscriptionTier.free:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription to cancel"
        )

    # TODO: Implement Stripe cancellation
    # This would typically involve:
    # 1. Cancel Stripe subscription at period end
    # 2. Update local record
    # 3. Send confirmation email

    return {
        "success": True,
        "message": "Your subscription has been scheduled for cancellation at the end of the current billing period",
        "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        "note": "This is a demo response. Stripe integration would be implemented here."
    }


@router.post("/reactivate")
async def reactivate_subscription(
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Reactivate a cancelled subscription (owner only).

    Args:
        owner: Current tenant owner
        db: Database session

    Returns:
        Reactivation result
    """
    # Get user's subscription (direct relationship: User -> Subscription)
    subscription = None
    if hasattr(owner, 'subscription') and owner.subscription:
        subscription = owner.subscription
    else:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == owner.id
        ).first()

    if not subscription or not subscription.cancel_at_period_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No cancelled subscription to reactivate"
        )

    # TODO: Implement Stripe reactivation
    # This would typically involve:
    # 1. Update Stripe subscription to not cancel at period end
    # 2. Update local record
    # 3. Send confirmation email

    return {
        "success": True,
        "message": "Your subscription has been reactivated and will continue after the current billing period",
        "note": "This is a demo response. Stripe integration would be implemented here."
    }