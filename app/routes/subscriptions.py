# app/routes/subscriptions.py
"""
Subscription management routes - 1-month Pro trial for new users.
After trial expires, users are downgraded to Free tier.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import get_settings
from app.core.models import User, Subscription, SubscriptionTier, SubscriptionStatus
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

# Trial period configuration
TRIAL_DURATION_DAYS = 30


# Response Models
class SubscriptionStatusResponse(BaseModel):
    """User subscription status response"""
    tier: str
    status: Optional[str]
    stripe_customer_id: Optional[str]
    current_period_end: Optional[str]
    cancel_at_period_end: bool
    can_access_pdf: bool
    can_access_export: bool
    stripe_available: bool = False
    region_message: Optional[str] = None
    # Trial period fields
    is_trial: bool = False
    trial_ends_at: Optional[str] = None
    trial_days_remaining: Optional[int] = None


class CheckoutSessionResponse(BaseModel):
    """Stripe checkout session response"""
    checkout_url: str
    session_id: str


class PortalSessionResponse(BaseModel):
    """Stripe portal session response"""
    portal_url: str


class CreateCheckoutRequest(BaseModel):
    """Request to create a checkout session"""
    price_type: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


def get_or_create_subscription(db: Session, user: User) -> Subscription:
    """Get existing subscription or create a 1-month Pro trial subscription for new users."""
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()

    if not subscription:
        # Create 1-month Pro trial for new users
        trial_ends_at = datetime.now(timezone.utc) + timedelta(days=TRIAL_DURATION_DAYS)
        subscription = Subscription(
            user_id=user.id,
            tenant_id=user.tenant_id,
            tier=SubscriptionTier.pro,  # Pro during trial
            status=SubscriptionStatus.active,
            is_trial=True,
            trial_ends_at=trial_ends_at
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

    return subscription


def check_and_expire_trial(subscription: Subscription, db: Session) -> Subscription:
    """Check if trial has expired and downgrade to Free if so."""
    if subscription.is_trial and subscription.trial_ends_at:
        now = datetime.now(timezone.utc)
        if subscription.trial_ends_at <= now:
            # Trial expired - downgrade to Free
            subscription.tier = SubscriptionTier.free
            subscription.is_trial = False
            subscription.status = None  # Free tier has no status
            db.commit()
            db.refresh(subscription)
    return subscription


def has_pro_access(subscription: Subscription) -> bool:
    """Check if user has Pro tier access (paid or active trial)."""
    # Pro tier or higher has access
    if subscription.tier in [SubscriptionTier.pro, SubscriptionTier.invoice_plus, SubscriptionTier.marketing_plus]:
        # If it's a trial, check if it's still active
        if subscription.is_trial and subscription.trial_ends_at:
            now = datetime.now(timezone.utc)
            return subscription.trial_ends_at > now
        return True
    return False


def get_trial_days_remaining(subscription: Subscription) -> Optional[int]:
    """Get the number of days remaining in the trial period."""
    if subscription.is_trial and subscription.trial_ends_at:
        now = datetime.now(timezone.utc)
        if subscription.trial_ends_at > now:
            delta = subscription.trial_ends_at - now
            return max(0, delta.days)
    return None


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's subscription status.
    New users get 1-month Pro trial. After trial expires, they are downgraded to Free.
    """
    subscription = get_or_create_subscription(db, current_user)

    # Check and expire trial if needed
    subscription = check_and_expire_trial(subscription, db)

    # Calculate trial info
    trial_days_remaining = get_trial_days_remaining(subscription)
    has_access = has_pro_access(subscription)

    # Build region message based on subscription state
    if subscription.is_trial and trial_days_remaining is not None:
        region_message = f"You have {trial_days_remaining} days remaining in your Pro trial. Upgrade to continue access after trial ends."
    elif subscription.tier == SubscriptionTier.free:
        region_message = "Your Pro trial has ended. Upgrade to Pro to unlock all features."
    else:
        region_message = "You have full Pro access."

    return SubscriptionStatusResponse(
        tier=subscription.tier.value,
        status=subscription.status.value if subscription.status else None,
        stripe_customer_id=subscription.stripe_customer_id,
        current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        cancel_at_period_end=subscription.cancel_at_period_end,
        can_access_pdf=has_access,
        can_access_export=has_access,
        stripe_available=False,
        region_message=region_message,
        # Trial fields
        is_trial=subscription.is_trial,
        trial_ends_at=subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
        trial_days_remaining=trial_days_remaining
    )


@router.post("/create-checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create checkout session - Disabled (Stripe not available in Cambodia).
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Payment processing is not yet available in your region. All Pro features are currently free during our beta period."
    )


@router.post("/create-portal", response_model=PortalSessionResponse)
async def create_portal_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create billing portal session - Disabled (Stripe not available in Cambodia).
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Payment processing is not yet available in your region. All Pro features are currently free during our beta period."
    )


@router.post("/webhook")
async def stripe_webhook():
    """
    Stripe webhook - Disabled (Stripe not available in Cambodia).
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Stripe webhooks are disabled"
    )


# Dependency for checking Pro tier access - Always grants access during beta
async def require_pro_tier(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that requires Pro tier subscription.
    During beta, all users have Pro access (Stripe not available in Cambodia).
    """
    # Everyone has Pro access during beta
    return current_user
