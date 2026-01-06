# app/routes/subscriptions.py
"""
Stripe subscription management routes for tiered feature access.
"""
import stripe
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
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


class CheckoutSessionResponse(BaseModel):
    """Stripe checkout session response"""
    checkout_url: str
    session_id: str


class PortalSessionResponse(BaseModel):
    """Stripe portal session response"""
    portal_url: str


class CreateCheckoutRequest(BaseModel):
    """Request to create a checkout session"""
    price_type: str  # "monthly" or "yearly"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


def get_stripe_client():
    """Initialize and return Stripe client"""
    settings = get_settings()
    secret_key = settings.STRIPE_SECRET_KEY.get_secret_value()
    if not secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured"
        )
    stripe.api_key = secret_key
    return stripe


def get_or_create_subscription(db: Session, user: User) -> Subscription:
    """Get existing subscription or create a free tier subscription for user"""
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()

    if not subscription:
        subscription = Subscription(
            user_id=user.id,
            tenant_id=user.tenant_id,
            tier=SubscriptionTier.free
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

    return subscription


def has_pro_access(subscription: Subscription) -> bool:
    """Check if user has Pro tier access"""
    if subscription.tier != SubscriptionTier.pro:
        return False

    # Check if subscription is active
    if subscription.status not in [SubscriptionStatus.active, None]:
        return False

    # Check if subscription hasn't expired
    if subscription.current_period_end:
        if subscription.current_period_end < datetime.now(timezone.utc):
            return False

    return True


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's subscription status.

    Returns tier information and feature access flags.
    """
    subscription = get_or_create_subscription(db, current_user)
    is_pro = has_pro_access(subscription)

    return SubscriptionStatusResponse(
        tier=subscription.tier.value,
        status=subscription.status.value if subscription.status else None,
        stripe_customer_id=subscription.stripe_customer_id,
        current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        cancel_at_period_end=subscription.cancel_at_period_end,
        can_access_pdf=is_pro,
        can_access_export=is_pro
    )


@router.post("/create-checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe checkout session for subscription purchase.

    Args:
        request: Contains price_type ("monthly" or "yearly")

    Returns:
        Checkout URL to redirect user to Stripe
    """
    settings = get_settings()
    stripe_client = get_stripe_client()

    # Get price ID based on type
    if request.price_type == "monthly":
        price_id = settings.STRIPE_PRICE_ID_MONTHLY
    elif request.price_type == "yearly":
        price_id = settings.STRIPE_PRICE_ID_YEARLY
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="price_type must be 'monthly' or 'yearly'"
        )

    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Stripe {request.price_type} price not configured"
        )

    subscription = get_or_create_subscription(db, current_user)

    # Use existing Stripe customer if available
    customer_id = subscription.stripe_customer_id

    # Create Stripe customer if doesn't exist
    if not customer_id:
        customer = stripe_client.Customer.create(
            email=current_user.email,
            metadata={
                "user_id": str(current_user.id),
                "tenant_id": str(current_user.tenant_id)
            }
        )
        customer_id = customer.id

        # Save customer ID
        subscription.stripe_customer_id = customer_id
        db.commit()

    # Build URLs
    frontend_url = str(settings.FRONTEND_URL).rstrip('/')
    success_url = request.success_url or f"{frontend_url}/dashboard/integrations?subscription=success"
    cancel_url = request.cancel_url or f"{frontend_url}/dashboard/integrations?subscription=cancelled"

    # Create checkout session
    try:
        checkout_session = stripe_client.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": str(current_user.id),
                "tenant_id": str(current_user.tenant_id)
            }
        )

        return CheckoutSessionResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.post("/create-portal", response_model=PortalSessionResponse)
async def create_portal_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe billing portal session for subscription management.

    Returns:
        Portal URL to redirect user to Stripe billing portal
    """
    settings = get_settings()
    stripe_client = get_stripe_client()

    subscription = get_or_create_subscription(db, current_user)

    if not subscription.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found. Please subscribe first."
        )

    frontend_url = str(settings.FRONTEND_URL).rstrip('/')
    return_url = f"{frontend_url}/dashboard/integrations"

    try:
        portal_session = stripe_client.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=return_url
        )

        return PortalSessionResponse(portal_url=portal_session.url)
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create portal session: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.

    Processes subscription lifecycle events:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    """
    settings = get_settings()
    stripe_client = get_stripe_client()

    webhook_secret = settings.STRIPE_WEBHOOK_SECRET.get_secret_value()
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured"
        )

    payload = await request.body()

    try:
        event = stripe_client.Webhook.construct_event(
            payload, stripe_signature, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    # Handle subscription events
    if event_type in ["customer.subscription.created", "customer.subscription.updated"]:
        await handle_subscription_update(db, data)
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(db, data)
    elif event_type == "invoice.payment_failed":
        await handle_payment_failed(db, data)

    return {"status": "received"}


async def handle_subscription_update(db: Session, stripe_subscription: dict):
    """Handle subscription created/updated events"""
    customer_id = stripe_subscription["customer"]
    subscription_id = stripe_subscription["id"]
    stripe_status = stripe_subscription["status"]

    # Find subscription by Stripe customer ID
    subscription = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()

    if not subscription:
        # Try to find by metadata
        return  # Can't process without matching subscription

    # Update subscription
    subscription.stripe_subscription_id = subscription_id
    subscription.tier = SubscriptionTier.pro

    # Map Stripe status to our status
    status_map = {
        "active": SubscriptionStatus.active,
        "past_due": SubscriptionStatus.past_due,
        "canceled": SubscriptionStatus.cancelled,
        "incomplete": SubscriptionStatus.incomplete,
        "incomplete_expired": SubscriptionStatus.cancelled,
        "trialing": SubscriptionStatus.active,
        "unpaid": SubscriptionStatus.past_due
    }
    subscription.status = status_map.get(stripe_status, SubscriptionStatus.incomplete)

    # Update period dates
    if "current_period_start" in stripe_subscription:
        subscription.current_period_start = datetime.fromtimestamp(
            stripe_subscription["current_period_start"], tz=timezone.utc
        )
    if "current_period_end" in stripe_subscription:
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_subscription["current_period_end"], tz=timezone.utc
        )

    subscription.cancel_at_period_end = stripe_subscription.get("cancel_at_period_end", False)

    db.commit()


async def handle_subscription_deleted(db: Session, stripe_subscription: dict):
    """Handle subscription deleted event"""
    customer_id = stripe_subscription["customer"]

    subscription = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()

    if subscription:
        subscription.tier = SubscriptionTier.free
        subscription.status = SubscriptionStatus.cancelled
        subscription.stripe_subscription_id = None
        db.commit()


async def handle_payment_failed(db: Session, invoice: dict):
    """Handle payment failed event"""
    customer_id = invoice["customer"]

    subscription = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()

    if subscription:
        subscription.status = SubscriptionStatus.past_due
        db.commit()


# Dependency for checking Pro tier access
async def require_pro_tier(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that requires Pro tier subscription.

    Use this in routes that need Pro tier access:
    @router.get("/protected")
    async def protected_route(user: User = Depends(require_pro_tier)):
        ...
    """
    subscription = get_or_create_subscription(db, current_user)

    if not has_pro_access(subscription):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "pro_required",
                "message": "This feature requires a Pro subscription",
                "upgrade_url": "/dashboard/integrations"
            }
        )

    return current_user
