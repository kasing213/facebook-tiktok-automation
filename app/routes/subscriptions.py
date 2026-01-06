# app/routes/subscriptions.py
"""
Subscription management routes - Stripe disabled (not available in Cambodia).
All users get Pro tier access for free during beta.
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import get_settings
from app.core.models import User, Subscription, SubscriptionTier, SubscriptionStatus
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


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
    """Get existing subscription or create a Pro tier subscription for user (beta period)"""
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()

    if not subscription:
        # Give everyone Pro tier during beta (Stripe not available in Cambodia)
        subscription = Subscription(
            user_id=user.id,
            tenant_id=user.tenant_id,
            tier=SubscriptionTier.pro,  # Pro for everyone during beta
            status=SubscriptionStatus.active
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

    return subscription


def has_pro_access(subscription: Subscription) -> bool:
    """Check if user has Pro tier access - Always true during beta"""
    # During beta, everyone has Pro access (Stripe not available in Cambodia)
    return True


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's subscription status.
    During beta, all users have Pro access for free.
    """
    subscription = get_or_create_subscription(db, current_user)

    return SubscriptionStatusResponse(
        tier="pro",  # Everyone is Pro during beta
        status="active",
        stripe_customer_id=None,
        current_period_end=None,
        cancel_at_period_end=False,
        can_access_pdf=True,  # All features enabled
        can_access_export=True,  # All features enabled
        stripe_available=False,
        region_message="All Pro features are free during our beta period. Payment processing will be available soon."
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
