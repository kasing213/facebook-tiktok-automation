# app/core/external_jwt.py
"""
JWT utilities for external service integration.

Provides JWT token generation and validation for communicating with external
services like the general-invoice API or other microservices.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from app.core.config import get_settings

# External JWT settings
EXTERNAL_ALGORITHM = "HS256"
EXTERNAL_TOKEN_EXPIRE_MINUTES = 60  # Longer for service-to-service communication


def create_external_service_token(
    service_name: str,
    tenant_id: str,
    user_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT token for external service authentication.

    Args:
        service_name: Name of the service (e.g., "invoice-api")
        tenant_id: The tenant ID for isolation
        user_id: Optional user ID
        data: Additional data to include in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    settings = get_settings()

    # Use dedicated external JWT secret or fallback to master secret
    jwt_secret = settings.INVOICE_JWT_SECRET.get_secret_value()
    if not jwt_secret:
        jwt_secret = settings.MASTER_SECRET_KEY.get_secret_value()

    to_encode = {
        "service": service_name,
        "tenant_id": str(tenant_id),
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4())
    }

    if user_id:
        to_encode["user_id"] = str(user_id)

    if data:
        to_encode.update(data)

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=EXTERNAL_TOKEN_EXPIRE_MINUTES)

    to_encode["exp"] = expire

    encoded_jwt = jwt.encode(to_encode, jwt_secret, algorithm=EXTERNAL_ALGORITHM)
    return encoded_jwt


def validate_external_service_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a JWT token from external service.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        settings = get_settings()

        # Use dedicated external JWT secret or fallback to master secret
        jwt_secret = settings.INVOICE_JWT_SECRET.get_secret_value()
        if not jwt_secret:
            jwt_secret = settings.MASTER_SECRET_KEY.get_secret_value()

        payload = jwt.decode(token, jwt_secret, algorithms=[EXTERNAL_ALGORITHM])
        return payload
    except JWTError:
        return None


def create_invoice_api_headers(tenant_id: str, user_id: Optional[str] = None) -> Dict[str, str]:
    """
    Create HTTP headers for Invoice API requests including JWT authentication.

    Args:
        tenant_id: The tenant ID for isolation
        user_id: Optional user ID

    Returns:
        Dict with Authorization header and other required headers
    """
    token = create_external_service_token(
        service_name="invoice-api",
        tenant_id=tenant_id,
        user_id=user_id
    )

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def create_general_invoice_client_token(tenant_id: str) -> str:
    """
    Create a JWT token specifically for general-invoice client integration.

    Args:
        tenant_id: The tenant ID for isolation

    Returns:
        JWT token for general-invoice service
    """
    return create_external_service_token(
        service_name="general-invoice",
        tenant_id=tenant_id,
        expires_delta=timedelta(hours=24)  # Longer expiry for client integration
    )


def extract_tenant_from_token(token: str) -> Optional[str]:
    """
    Extract tenant_id from a JWT token without full validation.

    Useful for routing and logging purposes.

    Args:
        token: JWT token string

    Returns:
        Tenant ID or None if not found
    """
    try:
        # Decode without verification to extract claims
        payload = jwt.get_unverified_claims(token)
        return payload.get("tenant_id")
    except Exception:
        return None