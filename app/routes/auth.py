# app/routes/auth.py
"""
Authentication routes for user login, registration, and password management.
"""
import datetime as dt
from datetime import timedelta
from typing import Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
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
from app.repositories import UserRepository, RefreshTokenRepository, TokenBlacklistRepository
from app.core.dependencies import get_current_user  # Shared dependency
from app.core.authorization import get_current_owner

router = APIRouter(prefix="/auth", tags=["authentication"])


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
    Register a new user account.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user data

    Raises:
        HTTPException: If username or email already exists
    """
    user_repo = UserRepository(db)

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

    # Create user
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

    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    User login with username and password.

    Args:
        request: FastAPI request object
        response: FastAPI response object (for setting cookies)
        form_data: OAuth2 password form (username, password)
        db: Database session

    Returns:
        JWT access token (refresh token set as httpOnly cookie)

    Raises:
        HTTPException: If credentials are invalid
    """
    user_repo = UserRepository(db)

    # Find user by username across all tenants
    # In production, you might want to require tenant_id for login
    user = user_repo.get_by_username_global(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not user.password_hash or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Update last login
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

    # Get device info and IP for security tracking
    device_info = request.headers.get("User-Agent", "")[:255]
    ip_address = request.client.host if request.client else None

    # Store refresh token in database
    refresh_repo = RefreshTokenRepository(db)
    refresh_repo.create_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        token_hash=refresh_token_hash,
        family_id=family_id,
        expires_at=refresh_expires_at,
        device_info=device_info,
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
