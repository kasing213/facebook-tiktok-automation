# app/routes/subscription_payment.py
"""
Subscription payment verification using local bank transfer + OCR verification.
Reuses the proven invoice + payment screenshot verification flow.
"""
from typing import Optional, List
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone, timedelta

from app.core.db import get_db
from app.core.models import User, SubscriptionTier, SubscriptionStatus
from app.core.authorization import get_current_owner
from app.services import invoice_mock_service as invoice_svc
from app.services.ocr_service import get_ocr_service


router = APIRouter(prefix="/subscription-payment", tags=["subscription_payment"])


# Request/Response Models
class SubscriptionUpgradeRequest(BaseModel):
    """Request to upgrade to Pro subscription"""
    tier: SubscriptionTier
    billing_cycle: str = "monthly"  # monthly, yearly
    customer_email: Optional[EmailStr] = None


class PaymentInstructionsResponse(BaseModel):
    """Payment instructions with QR code and bank details"""
    subscription_invoice_id: str
    amount_usd: float
    amount_khr: int
    bank_name: str
    account_number: str
    account_holder: str
    qr_code_data: str  # Base64 QR code image
    payment_reference: str
    expires_at: str
    instructions: List[str]


class PaymentVerificationRequest(BaseModel):
    """Payment verification request"""
    subscription_invoice_id: str


class PaymentVerificationResponse(BaseModel):
    """Payment verification response"""
    success: bool
    verification_status: str  # pending, verified, rejected
    message: str
    admin_approval_required: bool = True


# Subscription pricing
SUBSCRIPTION_PRICING = {
    SubscriptionTier.pro: {
        "monthly": {"usd": 29.99, "khr": 120000},
        "yearly": {"usd": 299.99, "khr": 1200000}  # 2 months free
    }
}

# Local bank details (replace with your actual bank info)
BANK_DETAILS = {
    "bank_name": "ACLEDA Bank",
    "account_number": "123-456-789",
    "account_holder": "Your Business Name",
    "currency": "KHR"
}


@router.post("/upgrade-request", response_model=PaymentInstructionsResponse)
async def request_subscription_upgrade(
    request: SubscriptionUpgradeRequest,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Create subscription upgrade invoice with payment instructions.

    This generates a special subscription invoice that includes:
    - QR code for local bank transfer
    - Payment instructions in local language
    - Reference number for payment tracking
    """
    # Validate pricing
    if request.tier not in SUBSCRIPTION_PRICING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pricing not available for tier: {request.tier}"
        )

    if request.billing_cycle not in SUBSCRIPTION_PRICING[request.tier]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Billing cycle '{request.billing_cycle}' not available"
        )

    # Get pricing
    pricing = SUBSCRIPTION_PRICING[request.tier][request.billing_cycle]

    # Generate unique payment reference
    payment_ref = f"SUB-{request.tier.value.upper()}-{owner.tenant_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Create subscription invoice using existing invoice system
    invoice_data = {
        "customer_id": "subscription_customer",  # Special customer for subscriptions
        "items": [
            {
                "description": f"{request.tier.value.title()} Subscription ({request.billing_cycle})",
                "quantity": 1,
                "unit_price": pricing["khr"],
                "tax_rate": 0
            }
        ],
        "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "notes": f"Subscription upgrade to {request.tier.value} plan",
        "currency": "KHR",
        "bank": BANK_DETAILS["bank_name"],
        "expected_account": BANK_DETAILS["account_number"],
        "recipient_name": BANK_DETAILS["account_holder"],
        "payment_reference": payment_ref
    }

    # Create the invoice record
    try:
        # Use direct database insertion for subscription invoices
        invoice_id = str(uuid4())

        # Insert into invoice table (matching your existing invoice schema)
        db.execute(text("""
            INSERT INTO invoice.invoice (
                id, customer_id, tenant_id, amount, currency, status,
                items, due_date, notes, bank, expected_account, recipient_name,
                invoice_number, customer_name,
                created_at, updated_at
            ) VALUES (
                :id, :customer_id, :tenant_id, :amount, :currency, 'pending',
                :items, :due_date, :notes, :bank, :expected_account, :recipient_name,
                :invoice_number, :customer_name,
                NOW(), NOW()
            )
        """), {
            "id": invoice_id,
            "customer_id": "subscription_customer",
            "tenant_id": str(owner.tenant_id),
            "amount": pricing["khr"],
            "currency": "KHR",
            "items": f'[{{"description": "{request.tier.value.title()} Subscription ({request.billing_cycle})", "quantity": 1, "unit_price": {pricing["khr"]}, "tax_rate": 0}}]',
            "due_date": (datetime.now() + timedelta(days=7)).date(),
            "notes": f"Subscription upgrade to {request.tier.value} plan - Payment Reference: {payment_ref}",
            "bank": BANK_DETAILS["bank_name"],
            "expected_account": BANK_DETAILS["account_number"],
            "recipient_name": BANK_DETAILS["account_holder"],
            "invoice_number": payment_ref,  # Use payment reference as invoice number
            "customer_name": f"Subscription for {owner.tenant.name if hasattr(owner, 'tenant') else 'Tenant'}"
        })
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription invoice: {str(e)}"
        )

    # Generate QR code for bank transfer (placeholder - replace with actual QR generation)
    qr_code_data = generate_bank_qr_code(
        bank_account=BANK_DETAILS["account_number"],
        amount=pricing["khr"],
        reference=payment_ref
    )

    # Payment instructions
    instructions = [
        f"1. Transfer {pricing['khr']:,} KHR to {BANK_DETAILS['bank_name']}",
        f"2. Account: {BANK_DETAILS['account_number']} ({BANK_DETAILS['account_holder']})",
        f"3. Reference: {payment_ref}",
        "4. Take screenshot of transaction confirmation",
        "5. Upload screenshot below for verification",
        "6. We'll verify and activate your Pro subscription within 30 seconds"
    ]

    return PaymentInstructionsResponse(
        subscription_invoice_id=invoice_id,
        amount_usd=pricing["usd"],
        amount_khr=pricing["khr"],
        bank_name=BANK_DETAILS["bank_name"],
        account_number=BANK_DETAILS["account_number"],
        account_holder=BANK_DETAILS["account_holder"],
        qr_code_data=qr_code_data,
        payment_reference=payment_ref,
        expires_at=(datetime.now() + timedelta(days=7)).isoformat(),
        instructions=instructions
    )


@router.post("/verify-payment", response_model=PaymentVerificationResponse)
async def verify_subscription_payment(
    subscription_invoice_id: str = Form(...),
    screenshot: UploadFile = File(...),
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Verify subscription payment by reusing the existing /verify-screenshot endpoint.

    This leverages your proven OCR verification system - same logic, same confidence checks.
    """
    # Get the subscription invoice
    result = db.execute(text("""
        SELECT id, amount, currency, bank, expected_account, recipient_name, status, notes
        FROM invoice.invoice
        WHERE id = :invoice_id AND tenant_id = :tenant_id AND customer_id = 'subscription_customer'
    """), {"invoice_id": subscription_invoice_id, "tenant_id": str(owner.tenant_id)})

    invoice = result.fetchone()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription invoice not found"
        )

    if invoice.status == "verified":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already verified and processed"
        )

    # Required field validation (matching your current OCR system)
    if not invoice.recipient_name or not invoice.expected_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="❌ Cannot verify payment. Invoice is missing required fields (recipient_name or expected_account)."
        )

    # Validate screenshot file (matching your current validation)
    if not screenshot.content_type or not screenshot.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a valid image file (PNG, JPG, etc.)"
        )

    if screenshot.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file too large. Maximum size is 10MB."
        )

    try:
        # Use the existing OCR service exactly like your invoice verification
        ocr_service = get_ocr_service()

        if not ocr_service.is_configured():
            raise HTTPException(
                status_code=503,
                detail="OCR service not configured. Set OCR_API_URL and OCR_API_KEY."
            )

        # Read image data
        image_data = await screenshot.read()
        if not image_data:
            raise HTTPException(status_code=400, detail="Empty image file")

        # Build expected payment (exact same format as your invoice OCR)
        expected_payment = {
            "amount": float(invoice.amount),
            "currency": invoice.currency or "KHR",
            "recipientNames": [invoice.recipient_name],  # Array format (from CLAUDE.md fix)
            "toAccount": invoice.expected_account,        # camelCase (from CLAUDE.md)
            "bank": invoice.bank
        }

        # Call OCR service (Mode A: no invoice_id to avoid MongoDB lookup)
        ocr_result = await ocr_service.verify_screenshot(
            image_data=image_data,
            filename=f"subscription_{subscription_invoice_id}_{screenshot.filename}",
            # No invoice_id parameter - forces Mode A (from CLAUDE.md fix)
            expected_payment=expected_payment,
            customer_id=str(owner.tenant_id)
        )

        # Extract results (matching your current pattern)
        extracted = ocr_result.get("extracted_data", {})
        verification = ocr_result.get("verification", {})
        confidence = ocr_result.get("confidence", 0)
        verification_warnings = verification.get("warnings") or []  # From CLAUDE.md fix

        is_verified = ocr_result.get("status") == "VERIFIED"

        # Process results with same confidence thresholds as your invoice system
        if is_verified and confidence >= 0.8:  # High confidence = auto-approve
            # Update database status
            db.execute(text("""
                UPDATE invoice.invoice
                SET status = 'verified',
                    verification_status = 'auto_approved',
                    verified_at = NOW(),
                    verification_confidence = :confidence,
                    verification_warnings = :warnings
                WHERE id = :invoice_id
            """), {
                "invoice_id": subscription_invoice_id,
                "confidence": confidence,
                "warnings": str(verification_warnings)
            })

            # Upgrade the subscription
            await upgrade_tenant_subscription(owner.tenant_id, SubscriptionTier.pro, db)
            db.commit()

            return PaymentVerificationResponse(
                success=True,
                verification_status="verified",
                message="✅ Payment verified! Your Pro subscription is now active.",
                admin_approval_required=False
            )

        elif is_verified:  # Lower confidence - require admin approval
            db.execute(text("""
                UPDATE invoice.invoice
                SET status = 'pending_approval',
                    verification_status = 'requires_approval',
                    verified_at = NOW(),
                    verification_confidence = :confidence,
                    verification_warnings = :warnings
                WHERE id = :invoice_id
            """), {
                "invoice_id": subscription_invoice_id,
                "confidence": confidence,
                "warnings": str(verification_warnings)
            })
            db.commit()

            return PaymentVerificationResponse(
                success=True,
                verification_status="pending_approval",
                message="⏳ Payment detected but requires manual approval. We'll review within 30 seconds.",
                admin_approval_required=True
            )

        else:  # Verification failed
            db.execute(text("""
                UPDATE invoice.invoice
                SET status = 'rejected',
                    verification_status = 'rejected',
                    verified_at = NOW(),
                    verification_confidence = :confidence
                WHERE id = :invoice_id
            """), {"invoice_id": subscription_invoice_id, "confidence": confidence})
            db.commit()

            return PaymentVerificationResponse(
                success=False,
                verification_status="rejected",
                message="❌ Could not verify payment from screenshot. Please ensure the image is clear and shows the complete transaction.",
                admin_approval_required=False
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


@router.post("/admin/approve/{subscription_invoice_id}")
async def admin_approve_subscription(
    subscription_invoice_id: str,
    approve: bool = True,
    admin_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to manually approve/reject subscription payments.

    Uses the same approval workflow as your regular invoice verification.
    """
    # Get the subscription invoice (same query pattern as your invoice system)
    result = db.execute(text("""
        SELECT id, tenant_id, amount, currency, status, verification_status, invoice_number, customer_name
        FROM invoice.invoice
        WHERE id = :invoice_id AND customer_id = 'subscription_customer'
    """), {"invoice_id": subscription_invoice_id})

    invoice = result.fetchone()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription invoice not found"
        )

    if invoice.verification_status != "requires_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice is not pending approval. Current status: {invoice.verification_status}"
        )

    if approve:
        # Approve and upgrade subscription (same field pattern as your invoice verification)
        db.execute(text("""
            UPDATE invoice.invoice
            SET status = 'verified',
                verification_status = 'admin_approved',
                verified_at = NOW(),
                admin_notes = :notes
            WHERE id = :invoice_id
        """), {"invoice_id": subscription_invoice_id, "notes": admin_notes})

        # Upgrade the subscription
        await upgrade_tenant_subscription(UUID(invoice.tenant_id), SubscriptionTier.pro, db)
        db.commit()

        return {
            "success": True,
            "message": f"✅ Subscription {invoice.invoice_number} approved and activated",
            "invoice_id": subscription_invoice_id,
            "tenant_id": invoice.tenant_id,
            "amount": f"{invoice.amount:,.0f} {invoice.currency}",
            "status": "verified"
        }
    else:
        # Reject the payment (same field pattern as your invoice verification)
        db.execute(text("""
            UPDATE invoice.invoice
            SET status = 'rejected',
                verification_status = 'admin_rejected',
                verified_at = NOW(),
                admin_notes = :notes
            WHERE id = :invoice_id
        """), {"invoice_id": subscription_invoice_id, "notes": admin_notes})
        db.commit()

        return {
            "success": False,
            "message": f"❌ Subscription {invoice.invoice_number} payment rejected",
            "invoice_id": subscription_invoice_id,
            "reason": admin_notes or "No reason provided",
            "status": "rejected"
        }


async def upgrade_tenant_subscription(tenant_id: UUID, tier: SubscriptionTier, db: Session):
    """Upgrade tenant subscription to the specified tier."""
    from app.core.models import Subscription

    # Check if subscription exists
    result = db.execute(text("""
        SELECT id FROM subscription WHERE tenant_id = :tenant_id
    """), {"tenant_id": str(tenant_id)})

    existing = result.fetchone()

    if existing:
        # Update existing subscription
        db.execute(text("""
            UPDATE subscription
            SET tier = :tier, status = 'active',
                current_period_start = NOW(),
                current_period_end = NOW() + INTERVAL '1 month',
                updated_at = NOW()
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": str(tenant_id), "tier": tier.value})
    else:
        # Create new subscription
        db.execute(text("""
            INSERT INTO subscription (
                id, tenant_id, user_id, tier, status,
                current_period_start, current_period_end,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :tenant_id,
                (SELECT id FROM "user" WHERE tenant_id = :tenant_id AND role = 'admin' LIMIT 1),
                :tier, 'active',
                NOW(), NOW() + INTERVAL '1 month',
                NOW(), NOW()
            )
        """), {"tenant_id": str(tenant_id), "tier": tier.value})


def generate_bank_qr_code(bank_account: str, amount: int, reference: str) -> str:
    """
    Generate QR code for bank transfer (placeholder implementation).

    Replace this with actual QR code generation for your local bank.
    Many banks provide QR code specifications for transfers.
    """
    import base64
    import json

    # Mock QR code data - replace with actual bank QR format
    qr_data = {
        "bank": BANK_DETAILS["bank_name"],
        "account": bank_account,
        "amount": amount,
        "currency": "KHR",
        "reference": reference
    }

    # For now, return base64 encoded JSON as placeholder
    # In production, generate actual QR code image
    qr_json = json.dumps(qr_data)
    qr_b64 = base64.b64encode(qr_json.encode()).decode()

    return f"data:image/png;base64,{qr_b64}"  # Placeholder format


@router.get("/admin/pending-approvals")
async def get_pending_subscription_approvals(
    db: Session = Depends(get_db)
):
    """
    Get list of subscription payments pending admin approval.

    TODO: Add admin authentication
    """
    result = db.execute(text("""
        SELECT
            i.id, i.tenant_id, i.amount, i.currency,
            i.created_at, i.verification_confidence, i.verification_warnings,
            t.name as tenant_name, t.slug as tenant_slug
        FROM invoice.invoice i
        JOIN tenant t ON t.id::text = i.tenant_id
        WHERE i.customer_id = 'subscription_customer'
          AND i.verification_status = 'requires_approval'
        ORDER BY i.created_at DESC
    """))

    pending_approvals = []
    for row in result:
        pending_approvals.append({
            "subscription_invoice_id": row.id,
            "tenant_id": row.tenant_id,
            "tenant_name": row.tenant_name,
            "tenant_slug": row.tenant_slug,
            "amount": float(row.amount),
            "currency": row.currency,
            "created_at": row.created_at.isoformat(),
            "confidence": row.verification_confidence,
            "warnings": row.verification_warnings
        })

    return {
        "pending_approvals": pending_approvals,
        "count": len(pending_approvals)
    }