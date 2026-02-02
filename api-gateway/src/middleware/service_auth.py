# api-gateway/src/middleware/service_auth.py
"""
Service authentication middleware for API Gateway.

Validates JWT tokens from internal services and provides context for internal API endpoints.
"""
import logging
from typing import Dict, Any
from fastapi import Header, HTTPException, status, Depends

from src.core.service_jwt import validate_service_token, extract_service_context, is_valid_service

logger = logging.getLogger(__name__)


class ServiceAuthError(HTTPException):
    """Custom exception for service authentication errors"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class UnauthorizedServiceError(HTTPException):
    """Exception for unauthorized service access"""
    def __init__(self, service: str = "unknown"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Service '{service}' is not authorized to access this endpoint"
        )


async def require_service_jwt(authorization: str = Header(..., alias="Authorization")) -> Dict[str, Any]:
    """
    FastAPI dependency to validate service JWT and extract context.

    Usage:
        @router.post("/internal/endpoint")
        async def internal_endpoint(context = Depends(require_service_jwt)):
            tenant_id = context["tenant_id"]
            user_id = context["user_id"]
            role = context["role"]

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Service context dict with tenant_id, user_id, role, service, request_id

    Raises:
        ServiceAuthError: If token is missing or invalid
        UnauthorizedServiceError: If service is not authorized
    """
    # Validate header format
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Missing or malformed Authorization header")
        raise ServiceAuthError("Missing or invalid authorization header")

    # Extract token
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        logger.warning("Empty JWT token in Authorization header")
        raise ServiceAuthError("Empty authorization token")

    # Validate JWT
    payload = validate_service_token(token)
    if not payload:
        logger.warning("Invalid JWT token received")
        raise ServiceAuthError("Invalid service token")

    # Validate service authorization
    if not is_valid_service(payload):
        service_name = payload.get("service", "unknown")
        logger.warning(f"Unauthorized service attempted access: {service_name}")
        raise UnauthorizedServiceError(service_name)

    # Extract context
    context = extract_service_context(payload)

    # Log successful authentication
    logger.info(
        f"Service auth success: service={context['service']}, "
        f"tenant_id={context['tenant_id']}, user_id={context['user_id']}, "
        f"role={context['role']}, request_id={context['request_id']}"
    )

    return context


async def require_service_jwt_optional(
    authorization: str = Header(None, alias="Authorization")
) -> Dict[str, Any]:
    """
    Optional service JWT validation for endpoints that can work with or without auth.

    Returns empty dict if no authorization provided, otherwise validates like require_service_jwt.
    """
    if not authorization:
        return {}

    return await require_service_jwt(authorization)