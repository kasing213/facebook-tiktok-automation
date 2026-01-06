# app/routes/billing.py
"""
Billing dashboard routes for payment history, billing overview, and payment method management.
"""
import stripe
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import get_settings
from app.core.models import User, Subscription, SubscriptionTier, SubscriptionStatus
from app.routes.auth import get_current_user
from app.routes.subscriptions import get_or_create_subscription, has_pro_access, get_stripe_client

router = APIRouter(prefix="/api/billing", tags=["billing"])


# Response Models
class PaymentMethodResponse(BaseModel):
    """Payment method details"""
    id: str
    type: str  # 'card' or 'bank_account'
    brand: Optional[str] = None
    last4: str
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    is_default: bool


class PaymentRecordResponse(BaseModel):
    """Payment/invoice record"""
    id: str
    date: str
    description: str
    amount: float
    currency: str
    status: str  # 'paid', 'pending', 'failed', 'refunded'
    invoice_url: Optional[str] = None
    invoice_pdf_url: Optional[str] = None
    receipt_url: Optional[str] = None


class PaginatedPaymentsResponse(BaseModel):
    """Paginated payment history"""
    payments: List[PaymentRecordResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class CurrentPlanResponse(BaseModel):
    """Current plan details"""
    name: str
    price: float
    billing_interval: Optional[str] = None


class NextPaymentResponse(BaseModel):
    """Next payment details"""
    date: Optional[str] = None
    amount: Optional[float] = None


class BillingOverviewResponse(BaseModel):
    """Full billing overview"""
    current_plan: CurrentPlanResponse
    this_month_cost: float
    budget_limit: Optional[float] = None
    budget_used_percent: float
    next_payment: NextPaymentResponse
    payment_method: Optional[PaymentMethodResponse] = None


@router.get("/overview", response_model=BillingOverviewResponse)
async def get_billing_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get billing overview including current plan, payment method, and next payment.
    """
    subscription = get_or_create_subscription(db, current_user)
    is_pro = has_pro_access(subscription)

    # Determine plan name and price
    if not is_pro:
        plan_name = "Free"
        plan_price = 0.0
        billing_interval = None
    else:
        # Try to determine if monthly or yearly based on Stripe subscription
        if subscription.stripe_subscription_id:
            try:
                stripe_client = get_stripe_client()
                stripe_sub = stripe_client.Subscription.retrieve(subscription.stripe_subscription_id)
                if stripe_sub.items.data:
                    item = stripe_sub.items.data[0]
                    interval = item.price.recurring.interval if item.price.recurring else 'month'
                    if interval == 'year':
                        plan_name = "Pro Yearly"
                        plan_price = 99.0
                        billing_interval = "year"
                    else:
                        plan_name = "Pro Monthly"
                        plan_price = 9.99
                        billing_interval = "month"
                else:
                    plan_name = "Pro"
                    plan_price = 9.99
                    billing_interval = "month"
            except Exception:
                plan_name = "Pro"
                plan_price = 9.99
                billing_interval = "month"
        else:
            plan_name = "Pro"
            plan_price = 9.99
            billing_interval = "month"

    # Get payment method
    payment_method = None
    if subscription.stripe_customer_id:
        try:
            stripe_client = get_stripe_client()
            payment_methods = stripe_client.PaymentMethod.list(
                customer=subscription.stripe_customer_id,
                type="card",
                limit=1
            )
            if payment_methods.data:
                pm = payment_methods.data[0]
                payment_method = PaymentMethodResponse(
                    id=pm.id,
                    type="card",
                    brand=pm.card.brand if pm.card else None,
                    last4=pm.card.last4 if pm.card else "****",
                    expiry_month=pm.card.exp_month if pm.card else None,
                    expiry_year=pm.card.exp_year if pm.card else None,
                    is_default=True
                )
        except Exception:
            pass

    # Calculate next payment
    next_payment_date = None
    next_payment_amount = None
    if is_pro and subscription.current_period_end:
        if not subscription.cancel_at_period_end:
            next_payment_date = subscription.current_period_end.isoformat()
            next_payment_amount = plan_price

    return BillingOverviewResponse(
        current_plan=CurrentPlanResponse(
            name=plan_name,
            price=plan_price,
            billing_interval=billing_interval
        ),
        this_month_cost=plan_price if is_pro else 0.0,
        budget_limit=None,  # Not using budgets for subscription model
        budget_used_percent=0.0,
        next_payment=NextPaymentResponse(
            date=next_payment_date,
            amount=next_payment_amount
        ),
        payment_method=payment_method
    )


@router.get("/payments", response_model=PaginatedPaymentsResponse)
async def get_payment_history(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated payment/invoice history from Stripe.
    """
    subscription = get_or_create_subscription(db, current_user)

    if not subscription.stripe_customer_id:
        return PaginatedPaymentsResponse(
            payments=[],
            total=0,
            page=page,
            page_size=page_size,
            has_more=False
        )

    try:
        stripe_client = get_stripe_client()

        # Fetch invoices from Stripe
        invoices = stripe_client.Invoice.list(
            customer=subscription.stripe_customer_id,
            limit=page_size,
            starting_after=None if page == 1 else None  # Stripe uses cursor-based pagination
        )

        payments = []
        for inv in invoices.data:
            # Determine status
            if inv.status == "paid":
                status = "paid"
            elif inv.status == "open":
                status = "pending"
            elif inv.status in ["uncollectible", "void"]:
                status = "failed"
            else:
                status = inv.status or "pending"

            # Get description from first line item or default
            description = "Subscription"
            if inv.lines and inv.lines.data:
                first_line = inv.lines.data[0]
                if first_line.description:
                    description = first_line.description
                elif first_line.price and first_line.price.nickname:
                    description = first_line.price.nickname

            payments.append(PaymentRecordResponse(
                id=inv.id,
                date=datetime.fromtimestamp(inv.created, tz=timezone.utc).isoformat(),
                description=description,
                amount=inv.amount_paid / 100.0 if inv.amount_paid else inv.amount_due / 100.0,
                currency=inv.currency.upper(),
                status=status,
                invoice_url=inv.hosted_invoice_url,
                invoice_pdf_url=inv.invoice_pdf,
                receipt_url=inv.charge.receipt_url if hasattr(inv, 'charge') and inv.charge and hasattr(inv.charge, 'receipt_url') else None
            ))

        return PaginatedPaymentsResponse(
            payments=payments,
            total=len(payments),  # Stripe doesn't provide total count easily
            page=page,
            page_size=page_size,
            has_more=invoices.has_more
        )

    except Exception as e:
        # Return empty on error to not break the UI
        return PaginatedPaymentsResponse(
            payments=[],
            total=0,
            page=page,
            page_size=page_size,
            has_more=False
        )


@router.get("/payments/{payment_id}", response_model=PaymentRecordResponse)
async def get_payment_detail(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a single payment/invoice detail.
    """
    subscription = get_or_create_subscription(db, current_user)

    if not subscription.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    try:
        stripe_client = get_stripe_client()
        inv = stripe_client.Invoice.retrieve(payment_id)

        # Verify this invoice belongs to the user's customer
        if inv.customer != subscription.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        # Determine status
        if inv.status == "paid":
            inv_status = "paid"
        elif inv.status == "open":
            inv_status = "pending"
        elif inv.status in ["uncollectible", "void"]:
            inv_status = "failed"
        else:
            inv_status = inv.status or "pending"

        description = "Subscription"
        if inv.lines and inv.lines.data:
            first_line = inv.lines.data[0]
            if first_line.description:
                description = first_line.description

        return PaymentRecordResponse(
            id=inv.id,
            date=datetime.fromtimestamp(inv.created, tz=timezone.utc).isoformat(),
            description=description,
            amount=inv.amount_paid / 100.0 if inv.amount_paid else inv.amount_due / 100.0,
            currency=inv.currency.upper(),
            status=inv_status,
            invoice_url=inv.hosted_invoice_url,
            invoice_pdf_url=inv.invoice_pdf,
            receipt_url=None
        )

    except stripe.error.InvalidRequestError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )


@router.get("/payment-method", response_model=Optional[PaymentMethodResponse])
async def get_payment_method(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the user's current payment method on file.
    """
    subscription = get_or_create_subscription(db, current_user)

    if not subscription.stripe_customer_id:
        return None

    try:
        stripe_client = get_stripe_client()
        payment_methods = stripe_client.PaymentMethod.list(
            customer=subscription.stripe_customer_id,
            type="card",
            limit=1
        )

        if not payment_methods.data:
            return None

        pm = payment_methods.data[0]
        return PaymentMethodResponse(
            id=pm.id,
            type="card",
            brand=pm.card.brand if pm.card else None,
            last4=pm.card.last4 if pm.card else "****",
            expiry_month=pm.card.exp_month if pm.card else None,
            expiry_year=pm.card.exp_year if pm.card else None,
            is_default=True
        )

    except Exception:
        return None
