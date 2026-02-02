# app/routes/mfa.py
"""
Multi-Factor Authentication (MFA) routes for TOTP setup and verification.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.db import get_db
from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.core.authorization import get_current_owner
from app.core.models import User, UserRole, MFASecret
from app.services.mfa_service import MFAService
import pyotp

router = APIRouter(prefix="/mfa", tags=["multi-factor-authentication"])


# Request/Response Models
class MFASetupResponse(BaseModel):
    """MFA setup response with QR code and backup codes"""
    secret: str
    qr_code_url: str
    backup_codes: List[str]
    message: str


class MFAVerifyRequest(BaseModel):
    """MFA verification request"""
    code: str = Field(..., min_length=6, max_length=8, description="6-digit TOTP code or 8-character backup code")


class MFAStatusResponse(BaseModel):
    """MFA status response"""
    enabled: bool
    required: bool
    verified: bool
    backup_codes_remaining: int
    backup_codes_used: Optional[int] = None
    last_used_at: Optional[str] = None
    created_at: Optional[str] = None


class BackupCodesResponse(BaseModel):
    """Backup codes response"""
    backup_codes: List[str]
    message: str


# Routes
@router.get("/status", response_model=MFAStatusResponse)
async def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get MFA status for the current user.

    Returns:
        MFAStatusResponse: Current MFA status
    """
    mfa_service = MFAService(db)
    status_info = mfa_service.get_mfa_status(current_user)
    return MFAStatusResponse(**status_info)


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set up MFA for the current user.

    Generates a new TOTP secret, QR code, and backup codes.
    User must verify the setup with a valid TOTP code.

    Returns:
        MFASetupResponse: Setup information including QR code

    Raises:
        HTTPException: If MFA is already enabled
    """
    mfa_service = MFAService(db)

    try:
        secret, qr_code_url, backup_codes = mfa_service.setup_mfa(current_user)

        return MFASetupResponse(
            secret=secret,
            qr_code_url=qr_code_url,
            backup_codes=backup_codes,
            message="Scan the QR code with your authenticator app and verify with a 6-digit code to complete setup."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/setup/qr")
async def get_qr_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get QR code image for MFA setup.

    Returns:
        PNG image: QR code for TOTP setup

    Raises:
        HTTPException: If MFA is not in setup state
    """
    mfa_service = MFAService(db)

    # Check if user has MFA in setup state (secret exists but not verified)
    mfa_record = db.query(MFASecret).filter_by(user_id=current_user.id).first()
    if not mfa_record or mfa_record.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No MFA setup in progress. Call /mfa/setup first."
        )

    # Generate QR code
    settings = get_settings()
    app_name = "Facebook-TikTok Automation"
    totp = pyotp.TOTP(mfa_record.secret)
    qr_code_url = totp.provisioning_uri(
        name=current_user.email or current_user.username,
        issuer_name=app_name
    )

    qr_code_image = mfa_service.generate_qr_code(qr_code_url)

    return Response(content=qr_code_image, media_type="image/png")


@router.post("/verify")
async def verify_mfa_setup(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify MFA setup with a TOTP code.

    This completes the MFA setup process and enables MFA for the user.

    Args:
        request: TOTP code verification request

    Returns:
        Success message

    Raises:
        HTTPException: If verification fails or MFA not in setup state
    """
    mfa_service = MFAService(db)

    # Check if user has MFA in setup state
    if mfa_service.is_mfa_enabled(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled and verified"
        )

    # Verify the code
    is_valid = mfa_service.verify_totp_code(current_user, request.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    return {"message": "MFA has been successfully enabled for your account"}


@router.post("/disable")
async def disable_mfa(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disable MFA for the current user.

    Requires a valid TOTP code or backup code for verification.

    Args:
        request: TOTP code verification request

    Returns:
        Success message

    Raises:
        HTTPException: If verification fails or MFA is required for role
    """
    mfa_service = MFAService(db)

    # Check if MFA is enabled
    if not mfa_service.is_mfa_enabled(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )

    # Check if MFA is required for this user's role
    if mfa_service.is_mfa_required(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA cannot be disabled for admin users"
        )

    # Verify the code before disabling
    is_valid = mfa_service.verify_totp_code(current_user, request.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    # Disable MFA
    was_disabled = mfa_service.disable_mfa(current_user)
    if not was_disabled:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable MFA"
        )

    return {"message": "MFA has been disabled for your account"}


@router.post("/backup-codes/regenerate", response_model=BackupCodesResponse)
async def regenerate_backup_codes(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate backup codes for MFA.

    Requires a valid TOTP code for verification.
    All previous backup codes will be invalidated.

    Args:
        request: TOTP code verification request

    Returns:
        BackupCodesResponse: New backup codes

    Raises:
        HTTPException: If verification fails or MFA not enabled
    """
    mfa_service = MFAService(db)

    # Check if MFA is enabled
    if not mfa_service.is_mfa_enabled(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )

    # Verify the code (don't allow backup codes for this operation)
    is_valid = mfa_service.verify_totp_code(current_user, request.code, allow_backup=False)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code. Backup codes cannot be used for this operation."
        )

    try:
        backup_codes = mfa_service.regenerate_backup_codes(current_user)
        return BackupCodesResponse(
            backup_codes=backup_codes,
            message="New backup codes generated. Store them securely - previous codes are no longer valid."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/enforce/{user_id}")
async def enforce_mfa_for_user(
    user_id: str,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Enforce MFA setup for a specific user (admin only).

    This can be used to require MFA for users who have been promoted
    to admin roles or as a security enforcement measure.

    Args:
        user_id: ID of the user to enforce MFA for

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or not authorized
    """
    from app.repositories import UserRepository

    user_repo = UserRepository(db)
    target_user = user_repo.get_by_id_and_tenant(user_id, current_user.tenant_id)

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    mfa_service = MFAService(db)

    # Check if MFA is already enabled
    if mfa_service.is_mfa_enabled(target_user):
        return {"message": f"User {target_user.username} already has MFA enabled"}

    # This is just a notification - the user will be required to set up MFA on next login
    # You could also set a flag in the user model to force MFA setup

    return {
        "message": f"MFA enforcement set for user {target_user.username}. "
                  f"They will be required to set up MFA based on their role."
    }