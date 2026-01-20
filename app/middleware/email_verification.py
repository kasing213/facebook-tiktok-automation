# app/middleware/email_verification.py
"""
Middleware to enforce email verification on protected endpoints.
Blocks unverified users from accessing core features.
"""
import logging
from typing import List, Set

from fastapi import HTTPException, status, Request, Response
from fastapi.responses import JSONResponse

from app.core.models import User

logger = logging.getLogger(__name__)

# Endpoints that require email verification
VERIFICATION_REQUIRED_PATHS: Set[str] = {
    # OAuth connections (high security)
    "/auth/facebook/authorize",
    "/auth/facebook/authorize-url",
    "/auth/tiktok/authorize",
    "/auth/tiktok/authorize-url",

    # Invoice operations (business critical)
    "/integrations/invoice/",  # All invoice endpoints
    "/api/integrations/invoice/",  # Alternative prefix

    # Telegram linking (security sensitive)
    "/telegram/generate-link-code",
    "/telegram/link-telegram",

    # User management (admin operations)
    "/users/",  # All user management

    # Subscription management (billing)
    "/subscription/",  # All subscription endpoints
    "/subscription-payment/",  # Payment operations

    # Inventory management
    "/inventory/",  # All inventory endpoints
}

# Paths that start with these prefixes require verification
VERIFICATION_REQUIRED_PREFIXES: List[str] = [
    "/integrations/invoice",
    "/api/integrations/invoice",
    "/users",
    "/subscription",
    "/inventory",
]

# Exempt paths that don't require verification even if user is authenticated
EXEMPT_PATHS: Set[str] = {
    # Authentication itself
    "/auth/login",
    "/auth/register",
    "/auth/refresh-token",
    "/auth/logout",
    "/auth/revoke-all-sessions",

    # Email verification endpoints
    "/auth/request-verification",
    "/auth/verify-email",
    "/auth/verification-status",
    "/auth/verification-required",

    # Public endpoints
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",

    # Static files
    "/policies",

    # System endpoints
    "/tiktokfIJT8p1JssnSfzGv35JP2RYDl3O7u5q0.txt",

    # Public tenant endpoints
    "/api/tenants",

    # Webhooks (external)
    "/api/webhooks",
}


def requires_email_verification(path: str) -> bool:
    """
    Check if a path requires email verification.

    Args:
        path: Request path to check

    Returns:
        bool: True if verification is required
    """
    # Remove query parameters
    clean_path = path.split("?")[0]

    # Check exempt paths first
    if clean_path in EXEMPT_PATHS:
        return False

    # Check exact matches
    if clean_path in VERIFICATION_REQUIRED_PATHS:
        return True

    # Check prefixes
    for prefix in VERIFICATION_REQUIRED_PREFIXES:
        if clean_path.startswith(prefix):
            return True

    return False


async def email_verification_middleware(request: Request, call_next):
    """
    Middleware to enforce email verification for protected endpoints.

    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint in chain

    Returns:
        Response: Either verification error or next response
    """
    try:
        # Check if this endpoint requires verification
        if not requires_email_verification(request.url.path):
            return await call_next(request)

        # Check if user is authenticated (has current_user in request state)
        user = getattr(request.state, 'current_user', None)
        if not user:
            # No user authenticated - let auth middleware handle it
            return await call_next(request)

        # Check if user's email is verified
        if not user.email_verified:
            logger.warning(
                f"Unverified user {user.id} attempted to access protected endpoint: {request.url.path}"
            )

            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Email verification required",
                    "message": "Please verify your email address to access this feature",
                    "verification_required": True,
                    "user_email": user.email,
                    "verification_endpoints": {
                        "request_verification": "/auth/request-verification",
                        "verification_status": "/auth/verification-status"
                    }
                }
            )

        # User is verified, continue to endpoint
        return await call_next(request)

    except Exception as e:
        logger.error(f"Email verification middleware error: {e}", exc_info=True)
        # On middleware error, return a safe error response
        # Don't try to call call_next again as it may have already been consumed
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error during request processing"}
        )


def create_verification_exception() -> HTTPException:
    """
    Create a standard email verification required exception.

    Returns:
        HTTPException: 403 error with verification details
    """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "message": "Email verification required to access this feature",
            "verification_required": True,
            "verification_endpoints": {
                "request_verification": "/auth/request-verification",
                "verification_status": "/auth/verification-status"
            }
        }
    )


def require_verified_email(user: User) -> None:
    """
    Decorator helper to check email verification in endpoint functions.

    Args:
        user: Current user object

    Raises:
        HTTPException: If email is not verified
    """
    if not user.email_verified:
        raise create_verification_exception()