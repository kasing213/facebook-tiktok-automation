# app/core/dependencies.py
"""
Shared FastAPI dependencies to avoid circular imports.
"""
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import User
from app.core.security import decode_access_token

# OAuth2 scheme for JWT token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        token: JWT access token from Authorization header
        db: Database session

    Returns:
        User object if valid

    Raises:
        HTTPException: If token is invalid or user not found
    """
    from app.repositories import UserRepository, TokenBlacklistRepository

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Check if token is blacklisted (logout, security revocation)
    jti = payload.get("jti")
    if jti:
        blacklist_repo = TokenBlacklistRepository(db)
        if blacklist_repo.is_blacklisted(jti):
            raise credentials_exception

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(UUID(user_id))

    if user is None or not user.is_active:
        raise credentials_exception

    return user
