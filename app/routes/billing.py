# app/routes/billing.py
"""
Billing dashboard routes - Stripe disabled (not available in Cambodia).
Returns placeholder data for billing UI.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/billing", tags=["billing"])


# Response Models
class PaymentMethodResponse(BaseModel):
    """Payment method details"""
    id: str
    type: str
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
    status: str
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
    stripe_available: bool = False
    region_message: Optional[str] = None


@router.get("/overview", response_model=BillingOverviewResponse)
async def get_billing_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get billing overview - Stripe disabled for Cambodia region.
    All users have Pro features enabled.
    """
    return BillingOverviewResponse(
        current_plan=CurrentPlanResponse(
            name="Pro (Free During Beta)",
            price=0.0,
            billing_interval=None
        ),
        this_month_cost=0.0,
        budget_limit=None,
        budget_used_percent=0.0,
        next_payment=NextPaymentResponse(
            date=None,
            amount=None
        ),
        payment_method=None,
        stripe_available=False,
        region_message="Payment processing is not yet available in your region. All Pro features are currently free during our beta period."
    )


@router.get("/payments", response_model=PaginatedPaymentsResponse)
async def get_payment_history(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment history - Returns empty as Stripe is disabled.
    """
    return PaginatedPaymentsResponse(
        payments=[],
        total=0,
        page=page,
        page_size=page_size,
        has_more=False
    )


@router.get("/payment-method")
async def get_payment_method(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment method - Returns null as Stripe is disabled.
    """
    return None
