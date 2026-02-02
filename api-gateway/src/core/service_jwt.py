# api-gateway/src/core/service_jwt.py
"""
Service JWT validation utilities for API Gateway.

Validates JWT tokens from internal services like facebook-automation backend.
Adapted from main backend's external_jwt.py module.
"""
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from src.config import settings

# Service JWT settings
SERVICE_ALGORITHM = "HS256"


def validate_service_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a JWT token from internal service.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        # Use MASTER_SECRET_KEY for validation (same as main backend)
        secret_key = settings.MASTER_SECRET_KEY
        if not secret_key:
            raise ValueError("MASTER_SECRET_KEY not configured")

        payload = jwt.decode(token, secret_key, algorithms=[SERVICE_ALGORITHM])
        return payload
    except JWTError:
        return None
    except Exception:
        return None


def extract_service_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract service context from validated JWT payload.

    Args:
        payload: Decoded JWT payload

    Returns:
        Service context dict with tenant_id, user_id, role, service
    """
    return {
        "service": payload.get("service"),
        "tenant_id": payload.get("tenant_id"),
        "user_id": payload.get("user_id"),
        "role": payload.get("role"),
        "request_id": payload.get("jti")
    }


def is_valid_service(payload: Dict[str, Any]) -> bool:
    """
    Check if the JWT payload represents a valid internal service.

    Args:
        payload: Decoded JWT payload

    Returns:
        True if service is authorized
    """
    service = payload.get("service")

    # Only allow facebook-automation backend
    if service != "facebook-automation":
        return False

    # Ensure required fields are present
    required_fields = ["tenant_id", "user_id", "role", "jti"]
    for field in required_fields:
        if not payload.get(field):
            return False

    return True