# app/core/security.py
"""
Security utilities for password hashing and JWT token generation.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import bcrypt
from jose import JWTError, jwt
from app.core.config import get_settings

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Reduced for enhanced security, refresh tokens provide UX
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # Convert password to bytes and generate salt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    # Hash the password
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string for database storage
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # Convert both to bytes
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    # Verify using bcrypt
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    settings = get_settings()
    # Use MASTER_SECRET_KEY for JWT encoding
    secret_key = settings.MASTER_SECRET_KEY.get_secret_value()

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token data or None if invalid
    """
    try:
        settings = get_settings()
        secret_key = settings.MASTER_SECRET_KEY.get_secret_value()

        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def create_access_token_with_jti(
    data: dict, expires_delta: Optional[timedelta] = None
) -> Tuple[str, str, datetime]:
    """
    Create a JWT access token with a unique JTI (JWT ID) claim.

    Args:
        data: Dictionary of data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Tuple of (encoded JWT token, JTI, expiration datetime)
    """
    to_encode = data.copy()
    jti = str(uuid.uuid4())

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "jti": jti})

    settings = get_settings()
    secret_key = settings.MASTER_SECRET_KEY.get_secret_value()

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt, jti, expire


def create_refresh_token() -> Tuple[str, str]:
    """
    Create a secure refresh token.

    Returns:
        Tuple of (raw token for cookie, SHA-256 hash for database storage)
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_refresh_token(raw_token)
    return raw_token, token_hash


def hash_refresh_token(token: str) -> str:
    """
    Hash a refresh token using SHA-256.

    Args:
        token: Raw refresh token string

    Returns:
        SHA-256 hex digest of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_refresh_token(raw_token: str, stored_hash: str) -> bool:
    """
    Verify a refresh token against its stored hash.

    Args:
        raw_token: The raw refresh token from the cookie
        stored_hash: The SHA-256 hash stored in the database

    Returns:
        True if the token matches, False otherwise
    """
    computed_hash = hash_refresh_token(raw_token)
    return secrets.compare_digest(computed_hash, stored_hash)
