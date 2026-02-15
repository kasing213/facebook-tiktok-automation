# app/middleware/security_headers.py
"""
Security headers middleware for FastAPI application.

Adds standard security headers to all HTTP responses to protect against
common web vulnerabilities (XSS, clickjacking, MIME sniffing, etc.).
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS - enforce HTTPS (Railway serves over HTTPS)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # Hide server implementation details
        response.headers.pop("Server", None)

        return response
