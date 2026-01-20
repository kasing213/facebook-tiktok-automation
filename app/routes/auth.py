# app/routes/auth.py
"""
Authentication routes for user login, registration, and password management.
"""
import datetime as dt
from datetime import timedelta
from typing import Optional
from uuid import UUID, uuid4
import secrets
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import get_settings
from app.core.models import User, UserRole
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_access_token_with_jti,
    create_refresh_token,
    hash_refresh_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.core.cookies import (
    set_refresh_token_cookie,
    clear_refresh_token_cookie,
    get_refresh_token_cookie_name,
)
from app.repositories import UserRepository, RefreshTokenRepository, TokenBlacklistRepository, EmailVerificationRepository, PasswordResetRepository
from app.core.dependencies import get_current_user  # Shared dependency
from app.core.authorization import get_current_owner
from app.services.email_service import EmailService, send_verification_email
from app.services.email_verification_service import EmailVerificationService
from app.services.login_attempt_service import LoginAttemptService
from app.core.models import LoginAttemptResult

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request headers"""
    # Check X-Forwarded-For first (for proxies like Railway/Vercel)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Check X-Real-IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct client host
    if request.client:
        return request.client.host

    return "unknown"


# Request/Response Models
class UserRegister(BaseModel):
    """User registration request"""
    tenant_id: UUID
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login request"""
    username: str
    password: str
    tenant_id: Optional[UUID] = None


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds


class UserResponse(BaseModel):
    """User data response"""
    id: UUID
    tenant_id: UUID
    username: Optional[str]
    email: Optional[str]
    role: UserRole
    is_active: bool
    email_verified: bool

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8)


# Note: get_current_user is imported from app.core.dependencies


# Routes
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user account with automatic email verification.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user data with verification status

    Raises:
        HTTPException: If username or email already exists
    """
    user_repo = UserRepository(db)
    email_verification_service = EmailVerificationService()
    email_service = EmailService()

    # Check if username already exists for this tenant
    existing_user = user_repo.get_by_username(user_data.tenant_id, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered for this organization"
        )

    # Check if email already exists for this tenant
    existing_email = user_repo.get_by_email(user_data.tenant_id, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered for this organization"
        )

    # Hash password
    password_hash = hash_password(user_data.password)

    # Determine role - first user in tenant becomes owner
    role = UserRole.admin if user_repo.is_first_user_in_tenant(user_data.tenant_id) else UserRole.user

    # Create user (email_verified=False by default)
    user = user_repo.create_user(
        tenant_id=user_data.tenant_id,
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        email_verified=False,
        role=role
    )

    db.commit()
    db.refresh(user)

    # Send verification email (non-blocking, errors logged but don't fail registration)
    try:
        verification_token = email_verification_service.generate_token(db, user)
        # Note: send_verification_email is synchronous, don't use await
        email_service.send_verification_email(user, verification_token)
    except Exception as e:
        # Log error but don't fail registration
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        # Continue with registration - user can request verification later

    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    User login with username and password including account lockout protection.

    Security Features:
    - Account lockout after 5 failed attempts (30 minutes)
    - Exponential backoff for repeat offenders
    - Login attempt logging for security monitoring

    Args:
        request: FastAPI request object
        response: FastAPI response object (for setting cookies)
        form_data: OAuth2 password form (username, password)
        db: Database session

    Returns:
        JWT access token (refresh token set as httpOnly cookie)

    Raises:
        HTTPException: If credentials are invalid or account is locked
    """
    # Initialize services
    user_repo = UserRepository(db)
    login_service = LoginAttemptService(db)

    # Get client information
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")[:255]
    email_attempted = form_data.username.lower()  # Normalize for consistency

    # Check if account is currently locked
    if login_service.is_account_locked(email_attempted):
        lockout_info = login_service.get_account_lockout_info(email_attempted)

        # Record the failed attempt (account locked)
        login_service.record_login_attempt(
            email=email_attempted,
            ip_address=ip_address,
            result=LoginAttemptResult.failure,
            user_agent=user_agent,
            failure_reason="account_locked"
        )

        if lockout_info:
            time_remaining = lockout_info.unlock_at - dt.datetime.now(dt.timezone.utc)
            minutes_remaining = int(time_remaining.total_seconds() / 60)

            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is temporarily locked due to too many failed login attempts. Try again in {minutes_remaining} minutes.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed login attempts.",
                headers={"WWW-Authenticate": "Bearer"}
            )

    # Find user by username across all tenants
    user = user_repo.get_by_username_global(form_data.username)

    # Validate user exists and password is correct
    credentials_valid = (
        user and
        user.password_hash and
        verify_password(form_data.password, user.password_hash)
    )

    if not credentials_valid:
        # Record failed attempt
        login_service.record_login_attempt(
            email=email_attempted,
            ip_address=ip_address,
            result=LoginAttemptResult.failure,
            user_agent=user_agent,
            failure_reason="invalid_credentials"
        )

        # Check if this should trigger account lockout
        was_locked, lockout_info = login_service.check_and_apply_lockout(email_attempted, ip_address)

        if was_locked:
            # Account was just locked
            time_remaining = lockout_info.unlock_at - dt.datetime.now(dt.timezone.utc)
            minutes_remaining = int(time_remaining.total_seconds() / 60)

            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Too many failed attempts. Account locked for {minutes_remaining} minutes.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        else:
            # Normal failed login response
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

    # Check if user account is active
    if not user.is_active:
        # Record failed attempt (inactive account)
        login_service.record_login_attempt(
            email=email_attempted,
            ip_address=ip_address,
            result=LoginAttemptResult.failure,
            user_agent=user_agent,
            failure_reason="account_inactive"
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Successful login - record the success
    login_service.record_login_attempt(
        email=email_attempted,
        ip_address=ip_address,
        result=LoginAttemptResult.success,
        user_agent=user_agent
    )

    # Update last login timestamp
    user_repo.update_last_login(user.id)

    # Create access token with JTI for blacklist support
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token, jti, token_exp = create_access_token_with_jti(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id)},
        expires_delta=access_token_expires
    )

    # Create refresh token
    raw_refresh_token, refresh_token_hash = create_refresh_token()
    family_id = uuid4()  # New token family for this login session
    refresh_expires_at = dt.datetime.now(dt.timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    # Store refresh token in database
    refresh_repo = RefreshTokenRepository(db)
    refresh_repo.create_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        token_hash=refresh_token_hash,
        family_id=family_id,
        expires_at=refresh_expires_at,
        device_info=user_agent,
        ip_address=ip_address,
    )

    db.commit()

    # Set refresh token as httpOnly cookie
    set_refresh_token_cookie(response, raw_refresh_token)

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from JWT token

    Returns:
        User data
    """
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.

    Args:
        password_data: Current and new password
        current_user: Current user from JWT token
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not current_user.password_hash or not verify_password(
        password_data.current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash new password
    new_password_hash = hash_password(password_data.new_password)

    # Update password
    user_repo = UserRepository(db)
    user_repo.update_password(current_user.id, new_password_hash)
    db.commit()

    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    User logout - blacklists current access token and revokes refresh token.

    Args:
        request: FastAPI request object
        response: FastAPI response object
        current_user: Current user from JWT token
        db: Database session

    Returns:
        Success message
    """
    # Get current access token and blacklist it
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = decode_access_token(token)
        if payload:
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                blacklist_repo = TokenBlacklistRepository(db)
                expires_at = dt.datetime.fromtimestamp(exp, tz=dt.timezone.utc)
                blacklist_repo.add_to_blacklist(
                    jti=jti,
                    user_id=current_user.id,
                    expires_at=expires_at,
                    reason="logout"
                )

    # Revoke refresh token from cookie
    cookie_name = get_refresh_token_cookie_name()
    refresh_token = request.cookies.get(cookie_name)
    if refresh_token:
        refresh_repo = RefreshTokenRepository(db)
        token_hash = hash_refresh_token(refresh_token)
        stored_token = refresh_repo.get_by_hash(token_hash)
        if stored_token:
            refresh_repo.revoke_token(stored_token.id)

    db.commit()

    # Clear refresh token cookie
    clear_refresh_token_cookie(response)

    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token from httpOnly cookie.
    Implements token rotation - old refresh token is invalidated.

    Args:
        request: FastAPI request object (contains refresh token cookie)
        response: FastAPI response object (for setting new cookie)
        db: Database session

    Returns:
        New JWT access token

    Raises:
        HTTPException: If refresh token is invalid, expired, or revoked
    """
    cookie_name = get_refresh_token_cookie_name()
    raw_refresh_token = request.cookies.get(cookie_name)

    if not raw_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find the refresh token in database
    token_hash = hash_refresh_token(raw_refresh_token)
    refresh_repo = RefreshTokenRepository(db)
    stored_token = refresh_repo.get_by_hash(token_hash)

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token was already revoked (potential token theft/reuse)
    if stored_token.revoked_at is not None:
        # Token reuse detected - revoke entire token family for security
        refresh_repo.revoke_family(stored_token.family_id)
        db.commit()
        clear_refresh_token_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token has expired
    now = dt.datetime.now(dt.timezone.utc)
    if stored_token.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(stored_token.user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token, jti, token_exp = create_access_token_with_jti(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id)},
        expires_delta=access_token_expires
    )

    # Rotate refresh token - create new one and revoke old
    new_raw_token, new_token_hash = create_refresh_token()
    refresh_expires_at = dt.datetime.now(dt.timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    device_info = request.headers.get("User-Agent", "")[:255]
    ip_address = request.client.host if request.client else None

    new_refresh_token = refresh_repo.create_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        token_hash=new_token_hash,
        family_id=stored_token.family_id,  # Keep same family for rotation tracking
        expires_at=refresh_expires_at,
        device_info=device_info,
        ip_address=ip_address,
    )

    # Revoke old refresh token (mark as replaced)
    refresh_repo.revoke_token(stored_token.id, replaced_by_id=new_refresh_token.id)

    db.commit()

    # Set new refresh token cookie
    set_refresh_token_cookie(response, new_raw_token)

    return Token(access_token=access_token)


@router.post("/revoke-all-sessions")
async def revoke_all_sessions(
    response: Response,
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Revoke all refresh tokens for the current user (logout from all devices).

    Args:
        response: FastAPI response object
        current_user: Current user from JWT token
        db: Database session

    Returns:
        Success message with count of revoked sessions
    """
    refresh_repo = RefreshTokenRepository(db)
    revoked_count = refresh_repo.revoke_user_tokens(current_user.id)
    db.commit()

    # Clear current session's cookie
    clear_refresh_token_cookie(response)

    return {
        "message": f"Successfully revoked {revoked_count} session(s)",
        "revoked_count": revoked_count
    }


@router.get("/sessions")
async def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active sessions for the current user.

    Args:
        current_user: Current user from JWT token
        db: Database session

    Returns:
        List of active sessions with device info
    """
    refresh_repo = RefreshTokenRepository(db)
    sessions = refresh_repo.get_user_active_sessions(current_user.id)

    return {
        "sessions": [
            {
                "id": str(session.id),
                "device_info": session.device_info,
                "ip_address": session.ip_address,
                "created_at": session.created_at.isoformat(),
                "expires_at": session.expires_at.isoformat(),
            }
            for session in sessions
        ],
        "count": len(sessions)
    }


# Email Verification Models
class VerifyEmailRequest(BaseModel):
    """Email verification request"""
    token: str


class SendVerificationEmailResponse(BaseModel):
    """Response for send verification email"""
    message: str


# Email Verification Endpoints
@router.post("/send-verification-email", response_model=SendVerificationEmailResponse)
async def send_verification_email_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send email verification link to the user's email address.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If email already verified or sending fails
    """
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )

    if not current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email address associated with this account"
        )

    settings = get_settings()

    # Generate secure token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    # Invalidate any existing tokens for this user
    verification_repo = EmailVerificationRepository(db)
    verification_repo.invalidate_user_tokens(current_user.id)

    # Create new token
    expires_at = dt.datetime.now(dt.timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS)
    verification_repo.create_token(
        user_id=current_user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )

    db.commit()

    # Build verification URL
    frontend_url = str(settings.FRONTEND_URL).rstrip('/')
    verification_url = f"{frontend_url}/verify-email?token={raw_token}"

    # Send email
    email_sent = send_verification_email(
        to_email=current_user.email,
        verification_url=verification_url,
        username=current_user.username or "User"
    )

    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )

    return {"message": "Verification email sent. Please check your inbox."}


@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email address using the token from the verification link.

    Args:
        request: Contains the verification token
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid, expired, or already used
    """
    # Hash the provided token
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()

    # Find the token
    verification_repo = EmailVerificationRepository(db)
    stored_token = verification_repo.get_by_token(token_hash)

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

    # Check if already used
    if stored_token.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link has already been used"
        )

    # Check if expired
    now = dt.datetime.now(dt.timezone.utc)
    if stored_token.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link has expired. Please request a new one."
        )

    # Mark token as used
    verification_repo.mark_as_used(stored_token.id)

    # Update user's email_verified status
    user_repo = UserRepository(db)
    user_repo.update(stored_token.user_id, email_verified=True)

    db.commit()

    return {"message": "Email verified successfully"}


# Password Reset Models
class ForgotPasswordRequest(BaseModel):
    """Forgot password request - sends reset email"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request - sets new password with token"""
    token: str
    new_password: str = Field(..., min_length=8)


# Password Reset Endpoints
@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset link.

    Always returns success message to prevent email enumeration.
    If the email exists, sends a password reset link.

    Args:
        request: Contains the user's email
        db: Database session

    Returns:
        Success message (always, even if email doesn't exist)
    """
    settings = get_settings()
    user_repo = UserRepository(db)
    reset_repo = PasswordResetRepository(db)
    email_service = EmailService()

    # Find user by email (across all tenants)
    user = user_repo.get_by_email_global(request.email)

    # Always return success to prevent email enumeration
    success_message = {"message": "If your email is registered, you will receive a password reset link shortly."}

    if not user:
        return success_message

    if not user.is_active:
        return success_message

    # Check rate limiting - don't send if recent token exists
    recent_token = reset_repo.get_recent_token_for_user(user.id, minutes=10)
    if recent_token:
        return success_message

    # Generate secure token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    # Invalidate any existing tokens for this user
    reset_repo.invalidate_user_tokens(user.id)

    # Create new token (expires in 1 hour for security)
    expires_at = dt.datetime.now(dt.timezone.utc) + timedelta(hours=1)
    reset_repo.create_token(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )

    db.commit()

    # Build reset URL
    frontend_url = str(settings.FRONTEND_URL).rstrip('/')
    reset_url = f"{frontend_url}/reset-password?token={raw_token}"

    # Send email (log if SMTP not configured)
    try:
        email_service.send_password_reset_email(user, reset_url)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send password reset email to {user.email}: {e}")

    return success_message


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using the token from the reset link.

    Args:
        request: Contains the reset token and new password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid, expired, or already used
    """
    # Hash the provided token
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()

    # Find the token
    reset_repo = PasswordResetRepository(db)
    stored_token = reset_repo.get_by_token(token_hash)

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset link"
        )

    # Check if already used
    if stored_token.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link has already been used"
        )

    # Check if expired
    now = dt.datetime.now(dt.timezone.utc)
    if stored_token.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link has expired. Please request a new one."
        )

    # Get the user
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(stored_token.user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account not found or inactive"
        )

    # Mark token as used
    reset_repo.mark_as_used(stored_token.id)

    # Update password
    new_password_hash = hash_password(request.new_password)
    user_repo.update_password(user.id, new_password_hash)

    # Revoke all existing sessions for security
    refresh_repo = RefreshTokenRepository(db)
    refresh_repo.revoke_user_tokens(user.id)

    db.commit()

    return {"message": "Password reset successfully. Please login with your new password."}
