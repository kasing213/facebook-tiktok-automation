"""OCR Verification Management API endpoints."""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.core.authorization import get_current_member_or_owner
from app.core.models import User
from app.services.ocr_audit_service import OCRAuditService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/verifications", tags=["verifications"])


# Pydantic models
class VerificationActionRequest(BaseModel):
    notes: Optional[str] = None


class PendingVerificationResponse(BaseModel):
    id: str
    invoice_number: str
    customer_name: str
    amount: float
    currency: str
    verification_status: str
    created_at: str
    screenshot_uploaded_at: Optional[str]
    confidence_score: Optional[float]
    ocr_notes: Optional[str]


class AuditTrailEntry(BaseModel):
    id: str
    action: str
    previous_status: Optional[str]
    new_status: str
    confidence_score: Optional[float]
    verified_by_name: str
    verification_method: Optional[str]
    notes: Optional[str]
    created_at: str


class VerificationStatsResponse(BaseModel):
    total_verifications: int
    auto_verified: int
    manual_actions: int
    avg_confidence: float
    actions_breakdown: List[Dict[str, Any]]


def _get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and user agent from request."""
    # Get real IP from headers (accounting for proxies)
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip:
        ip = request.headers.get("x-real-ip") or request.client.host

    user_agent = request.headers.get("user-agent")
    return ip, user_agent


@router.get("/pending", response_model=List[PendingVerificationResponse])
async def get_pending_verifications(
    limit: int = 50,
    skip: int = 0,
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Get list of pending payment verifications."""
    try:
        result = db.execute(
            text("""
                SELECT
                    i.id,
                    i.invoice_number,
                    COALESCE(c.name, 'Unknown Customer') as customer_name,
                    i.amount,
                    i.currency,
                    i.verification_status,
                    i.created_at,
                    i.updated_at as screenshot_uploaded_at,
                    NULL as confidence_score,
                    i.verification_note as ocr_notes
                FROM invoice.invoice i
                LEFT JOIN invoice.customer c ON i.customer_id = c.id
                WHERE i.tenant_id = :tenant_id
                AND i.verification_status IN ('pending', 'reviewing')
                ORDER BY i.created_at DESC
                LIMIT :limit OFFSET :skip
            """),
            {
                "tenant_id": str(current_user.tenant_id),
                "limit": limit,
                "skip": skip
            }
        )

        verifications = []
        for row in result:
            verification = PendingVerificationResponse(
                id=str(row.id),
                invoice_number=row.invoice_number,
                customer_name=row.customer_name,
                amount=float(row.amount),
                currency=row.currency,
                verification_status=row.verification_status,
                created_at=row.created_at.isoformat(),
                screenshot_uploaded_at=row.screenshot_uploaded_at.isoformat() if row.screenshot_uploaded_at else None,
                confidence_score=row.confidence_score,
                ocr_notes=row.ocr_notes
            )
            verifications.append(verification)

        return verifications

    except Exception as e:
        logger.error(f"Failed to get pending verifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pending verifications")


@router.get("/{invoice_id}/history", response_model=List[AuditTrailEntry])
async def get_verification_history(
    invoice_id: UUID,
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Get audit trail history for a specific invoice."""
    try:
        # Verify invoice belongs to tenant
        invoice_check = db.execute(
            text("SELECT id FROM invoice.invoice WHERE id = :invoice_id AND tenant_id = :tenant_id"),
            {"invoice_id": str(invoice_id), "tenant_id": str(current_user.tenant_id)}
        )

        if not invoice_check.fetchone():
            raise HTTPException(status_code=404, detail="Invoice not found")

        audit_entries = OCRAuditService.get_invoice_audit_trail(
            db=db,
            invoice_id=invoice_id,
            tenant_id=current_user.tenant_id
        )

        return [AuditTrailEntry(**entry) for entry in audit_entries]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get verification history for {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve verification history")


@router.post("/{invoice_id}/approve")
async def approve_verification(
    invoice_id: UUID,
    request_data: VerificationActionRequest,
    request: Request,
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Manually approve a payment verification."""
    try:
        # Get current invoice status
        invoice_result = db.execute(
            text("""
                SELECT verification_status, amount, customer_id
                FROM invoice.invoice
                WHERE id = :invoice_id AND tenant_id = :tenant_id
            """),
            {"invoice_id": str(invoice_id), "tenant_id": str(current_user.tenant_id)}
        )

        invoice_row = invoice_result.fetchone()
        if not invoice_row:
            raise HTTPException(status_code=404, detail="Invoice not found")

        previous_status = invoice_row.verification_status

        # Update invoice status to verified
        db.execute(
            text("""
                UPDATE invoice.invoice
                SET verification_status = 'verified',
                    verified_at = NOW(),
                    verified_by = :verified_by,
                    verification_note = :notes
                WHERE id = :invoice_id AND tenant_id = :tenant_id
            """),
            {
                "invoice_id": str(invoice_id),
                "tenant_id": str(current_user.tenant_id),
                "verified_by": current_user.email,
                "notes": request_data.notes or "Manually approved via web dashboard"
            }
        )

        # Get client info
        ip_address, user_agent = _get_client_info(request)

        # Log audit trail
        OCRAuditService.log_manual_action(
            db=db,
            tenant_id=current_user.tenant_id,
            invoice_id=invoice_id,
            action="manual_approved",
            verified_by=current_user,
            notes=request_data.notes,
            ip_address=ip_address,
            user_agent=user_agent,
            verification_method="manual_web",
            previous_status=previous_status
        )

        db.commit()

        # TODO: Deduct stock if configured
        # TODO: Send notification to customer/merchant

        return {
            "success": True,
            "message": "Payment verification approved successfully",
            "invoice_id": str(invoice_id),
            "status": "verified"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve verification for {invoice_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to approve verification")


@router.post("/{invoice_id}/reject")
async def reject_verification(
    invoice_id: UUID,
    request_data: VerificationActionRequest,
    request: Request,
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Manually reject a payment verification."""
    try:
        # Get current invoice status
        invoice_result = db.execute(
            text("""
                SELECT verification_status
                FROM invoice.invoice
                WHERE id = :invoice_id AND tenant_id = :tenant_id
            """),
            {"invoice_id": str(invoice_id), "tenant_id": str(current_user.tenant_id)}
        )

        invoice_row = invoice_result.fetchone()
        if not invoice_row:
            raise HTTPException(status_code=404, detail="Invoice not found")

        previous_status = invoice_row.verification_status

        # Update invoice status to rejected
        db.execute(
            text("""
                UPDATE invoice.invoice
                SET verification_status = 'rejected',
                    verified_at = NOW(),
                    verified_by = :verified_by,
                    verification_note = :notes
                WHERE id = :invoice_id AND tenant_id = :tenant_id
            """),
            {
                "invoice_id": str(invoice_id),
                "tenant_id": str(current_user.tenant_id),
                "verified_by": current_user.email,
                "notes": request_data.notes or "Manually rejected via web dashboard"
            }
        )

        # Get client info
        ip_address, user_agent = _get_client_info(request)

        # Log audit trail
        OCRAuditService.log_manual_action(
            db=db,
            tenant_id=current_user.tenant_id,
            invoice_id=invoice_id,
            action="manual_rejected",
            verified_by=current_user,
            notes=request_data.notes,
            ip_address=ip_address,
            user_agent=user_agent,
            verification_method="manual_web",
            previous_status=previous_status
        )

        db.commit()

        # TODO: Send rejection notification

        return {
            "success": True,
            "message": "Payment verification rejected successfully",
            "invoice_id": str(invoice_id),
            "status": "rejected"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject verification for {invoice_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reject verification")


@router.post("/{invoice_id}/review")
async def mark_for_review(
    invoice_id: UUID,
    request_data: VerificationActionRequest,
    request: Request,
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Mark verification for manual review."""
    try:
        # Get current invoice status
        invoice_result = db.execute(
            text("""
                SELECT verification_status
                FROM invoice.invoice
                WHERE id = :invoice_id AND tenant_id = :tenant_id
            """),
            {"invoice_id": str(invoice_id), "tenant_id": str(current_user.tenant_id)}
        )

        invoice_row = invoice_result.fetchone()
        if not invoice_row:
            raise HTTPException(status_code=404, detail="Invoice not found")

        previous_status = invoice_row.verification_status

        # Update invoice status to reviewing
        db.execute(
            text("""
                UPDATE invoice.invoice
                SET verification_status = 'reviewing',
                    verification_note = :notes
                WHERE id = :invoice_id AND tenant_id = :tenant_id
            """),
            {
                "invoice_id": str(invoice_id),
                "tenant_id": str(current_user.tenant_id),
                "notes": request_data.notes or "Marked for manual review"
            }
        )

        # Get client info
        ip_address, user_agent = _get_client_info(request)

        # Log audit trail
        OCRAuditService.log_manual_action(
            db=db,
            tenant_id=current_user.tenant_id,
            invoice_id=invoice_id,
            action="manual_pending",
            verified_by=current_user,
            notes=request_data.notes,
            ip_address=ip_address,
            user_agent=user_agent,
            verification_method="manual_web",
            previous_status=previous_status
        )

        db.commit()

        return {
            "success": True,
            "message": "Payment marked for review successfully",
            "invoice_id": str(invoice_id),
            "status": "reviewing"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark verification for review {invoice_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to mark for review")


@router.get("/stats", response_model=VerificationStatsResponse)
async def get_verification_stats(
    days: int = 30,
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Get verification statistics for the current tenant."""
    try:
        stats = OCRAuditService.get_verification_stats(
            db=db,
            tenant_id=current_user.tenant_id,
            days=days
        )

        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])

        return VerificationStatsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get verification stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve verification statistics")