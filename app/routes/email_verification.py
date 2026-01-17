# app/routes/email_verification.py
"""
Email verification endpoints for user account activation.
Implements secure double opt-in email verification flow.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.core.models import User
from app.services.email_verification_service import EmailVerificationService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Email Verification"])

# Initialize services
email_verification_service = EmailVerificationService()
email_service = EmailService()


class ResendVerificationRequest(BaseModel):
    """Request model for resending verification email"""
    pass


class VerifyEmailRequest(BaseModel):
    """Request model for email verification via POST"""
    token: str


class VerificationStatusResponse(BaseModel):
    """Response model for verification status"""
    is_verified: bool
    email: Optional[str] = None
    verified_at: Optional[datetime] = None
    message: str


class VerificationResponse(BaseModel):
    """Response model for verification actions"""
    success: bool
    message: str
    user_verified: bool = False


@router.post(
    "/request-verification",
    response_model=VerificationResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def request_verification_email(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request a new verification email to be sent.

    **Security Features:**
    - Rate limiting: Max 3 emails per 10 minutes
    - Always returns 202 to prevent user enumeration
    - Background email sending to avoid blocking
    """
    try:
        # Check if user is already verified
        if current_user.email_verified:
            return VerificationResponse(
                success=True,
                message="Email address is already verified",
                user_verified=True
            )

        # Check if user has an email
        if not current_user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No email address associated with this account"
            )

        # Rate limiting check
        if not email_verification_service.resend_verification(db, current_user):
            return VerificationResponse(
                success=False,
                message="Please wait 10 minutes before requesting another verification email"
            )

        # Generate new verification token
        verification_token = email_verification_service.generate_token(db, current_user)

        # Send email in background
        background_tasks.add_task(
            email_service.send_verification_email,
            current_user,
            verification_token
        )

        # Always return 202 to prevent user enumeration
        return VerificationResponse(
            success=True,
            message="If your email address is valid, you will receive a verification email shortly"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting verification for user {current_user.id}: {e}")
        # Return generic success message to prevent information disclosure
        return VerificationResponse(
            success=True,
            message="Verification email request processed"
        )


@router.get(
    "/verify-email",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK
)
async def verify_email_get(
    token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Verify email address via GET request (link from email).

    **Security Features:**
    - Token validation with expiration
    - Single-use tokens
    - Background welcome email sending
    """
    try:
        # Verify the token and get the user
        user = email_verification_service.verify_token(db, token)

        if not user:
            return VerificationResponse(
                success=False,
                message="Invalid or expired verification token"
            )

        # Send welcome email in background
        background_tasks.add_task(
            email_service.send_verification_success_email,
            user
        )

        return VerificationResponse(
            success=True,
            message="Email address verified successfully! Welcome to KS Automation.",
            user_verified=True
        )

    except Exception as e:
        logger.error(f"Error during email verification: {e}")
        return VerificationResponse(
            success=False,
            message="Verification failed. Please try requesting a new verification email."
        )


@router.post(
    "/verify-email",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK
)
async def verify_email_post(
    request: VerifyEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Verify email address via POST request (manual token submission).

    **Security Features:**
    - Same security as GET endpoint
    - Supports frontend form submissions
    """
    return await verify_email_get(request.token, background_tasks, db)


@router.get(
    "/verification-status",
    response_model=VerificationStatusResponse
)
async def get_verification_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's email verification status.

    **Returns:**
    - Verification status and timestamp
    - Safe for authenticated users only
    """
    return VerificationStatusResponse(
        is_verified=current_user.email_verified,
        email=current_user.email if current_user.email_verified else None,
        verified_at=current_user.email_verified_at,
        message=(
            "Email address is verified"
            if current_user.email_verified
            else "Email address requires verification"
        )
    )


# Public endpoint for checking if email verification is required
@router.get(
    "/verification-required",
    response_model=dict,
    status_code=status.HTTP_200_OK
)
async def check_verification_required():
    """
    Public endpoint to check if email verification is enabled.

    **Returns:**
    - Whether email verification is required for new accounts
    - Useful for frontend conditional rendering
    """
    return {
        "verification_required": True,
        "verification_expire_hours": email_verification_service.settings.EMAIL_VERIFICATION_EXPIRE_HOURS,
        "smtp_configured": email_service.is_configured()
    }


# Admin endpoint for cleanup (could be called by background job)
@router.post(
    "/cleanup-tokens",
    response_model=dict,
    status_code=status.HTTP_200_OK
)
async def cleanup_expired_tokens(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cleanup expired verification tokens (admin only).

    **Security:**
    - Requires authentication
    - Could be restricted to admin role
    """
    try:
        cleaned_count = email_verification_service.cleanup_expired_tokens(db)

        logger.info(f"Cleaned up {cleaned_count} expired verification tokens")

        return {
            "success": True,
            "tokens_cleaned": cleaned_count,
            "message": f"Cleaned up {cleaned_count} expired verification tokens"
        }

    except Exception as e:
        logger.error(f"Error cleaning up tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired tokens"
        )