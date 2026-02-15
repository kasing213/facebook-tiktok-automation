# app/middleware/rate_limit.py
"""
Rate limiting middleware with IP blocking support

Implements per-IP rate limiting with automatic banning and whitelist/blacklist support.
Includes suspicious path detection to block vulnerability scanners before database queries.
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging

from app.core.config import get_settings
from app.core.rate_limit_store import RateLimitStore
from app.core.db import SessionLocal
from app.repositories.ip_access import IPAccessRepository
from app.core.models import IPRuleType

_logger = logging.getLogger("app.middleware.rate_limit")

# Patterns commonly probed by vulnerability scanners.
# Requests matching these are immediately rejected with 404 before any DB query.
SUSPICIOUS_PATTERNS = [
    '.env', '.git', '.svn', '.hg',
    'phpinfo', '.php',
    'wp-admin', 'wp-login', 'wp-content', 'wordpress',
    'phpmyadmin', 'pma',
    '.sql', '.bak', '.backup',
    '.aws', '.htaccess', '.htpasswd',
    'web.config', 'docker-compose',
    '_profiler',
]


def get_client_ip(request: Request, trust_proxy: bool = True) -> str:
    """
    Extract client IP address from request

    Args:
        request: FastAPI request object
        trust_proxy: Whether to trust X-Forwarded-For headers

    Returns:
        Client IP address as string
    """
    if trust_proxy:
        # Check X-Forwarded-For first (for Railway, Vercel, proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For can be comma-separated list, take first IP
            return forwarded.split(",")[0].strip()

        # Check other proxy headers
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

    # Fallback to direct client host
    if request.client:
        return request.client.host

    return "unknown"


def _is_suspicious_path(path: str) -> bool:
    """Check if a request path matches known vulnerability scanner patterns."""
    path_lower = path.lower()
    return any(pattern in path_lower for pattern in SUSPICIOUS_PATTERNS)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting and IP blocking

    Features:
    - Per-IP rate limiting (configurable requests per minute)
    - IP whitelist (bypass rate limiting)
    - IP blacklist (block immediately with 403)
    - Automatic IP banning after repeated violations
    - Suspicious path detection (blocks scanners before DB queries)
    - Returns 429 with Retry-After header
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.settings = get_settings()
        self.rate_limit_store = RateLimitStore(redis_url=self.settings.REDIS_URL)

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting and IP blocking"""

        # Get client IP
        client_ip = get_client_ip(request, self.settings.TRUST_PROXY_HEADERS)

        # Skip rate limiting for health check and static files
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        if request.url.path.startswith("/policies/"):
            return await call_next(request)

        # Block suspicious scanner paths immediately (no DB query needed)
        if _is_suspicious_path(request.url.path):
            _logger.warning(
                "Vulnerability scan blocked: %s %s from %s (UA: %s)",
                request.method,
                request.url.path,
                client_ip,
                request.headers.get("user-agent", "unknown"),
            )
            return JSONResponse(
                status_code=404,
                content={"detail": "Not found"}
            )

        # Check IP access rules using database (with fail-open error handling)
        current_count = 0
        try:
            with SessionLocal() as session:
                ip_repo = IPAccessRepository(session)

                # 1. Check whitelist (always allow, bypass rate limiting)
                if ip_repo.is_ip_whitelisted(client_ip):
                    return await call_next(request)

                # 2. Check blacklist (immediate block)
                if ip_repo.is_ip_blacklisted(client_ip):
                    return JSONResponse(
                        status_code=403,
                        content={
                            "detail": "Access denied",
                            "error": "forbidden",
                            "ip": client_ip
                        }
                    )

                # 3. Check auto-ban (temporary ban from violations)
                if ip_repo.is_ip_auto_banned(client_ip):
                    retry_after = self.rate_limit_store.get_retry_after(client_ip, window=self.settings.RATE_LIMIT_AUTO_BAN_DURATION)
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": "Too many violations. Temporarily banned.",
                            "error": "too_many_requests",
                            "retry_after": retry_after,
                            "ip": client_ip
                        },
                        headers={"Retry-After": str(retry_after)}
                    )

                # 4. Rate limiting check
                rate_limit_key = f"ip:{client_ip}"
                current_count = self.rate_limit_store.increment(rate_limit_key, window=60)

                if current_count > self.settings.RATE_LIMIT_PER_MINUTE:
                    # Rate limit exceeded
                    retry_after = self.rate_limit_store.get_retry_after(rate_limit_key, window=60)

                    # Record violation in database
                    ip_repo.record_violation(client_ip, request.url.path)

                    # Check if we should auto-ban
                    violations_count = ip_repo.get_violations_count(client_ip, time_window=3600)  # Last hour

                    if violations_count >= self.settings.RATE_LIMIT_VIOLATION_THRESHOLD:
                        # Auto-ban this IP
                        ip_repo.auto_ban_ip(
                            ip=client_ip,
                            reason=f"Automatic ban due to {violations_count} rate limit violations in 1 hour",
                            duration_seconds=self.settings.RATE_LIMIT_AUTO_BAN_DURATION
                        )

                        return JSONResponse(
                            status_code=429,
                            content={
                                "detail": f"Too many violations. Automatically banned for {self.settings.RATE_LIMIT_AUTO_BAN_DURATION // 3600} hours.",
                                "error": "too_many_requests",
                                "retry_after": self.settings.RATE_LIMIT_AUTO_BAN_DURATION,
                                "ip": client_ip,
                                "violations": violations_count
                            },
                            headers={"Retry-After": str(self.settings.RATE_LIMIT_AUTO_BAN_DURATION)}
                        )

                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": f"Rate limit exceeded. Maximum {self.settings.RATE_LIMIT_PER_MINUTE} requests per minute.",
                            "error": "too_many_requests",
                            "retry_after": retry_after,
                            "ip": client_ip,
                            "current_count": current_count,
                            "limit": self.settings.RATE_LIMIT_PER_MINUTE
                        },
                        headers={"Retry-After": str(retry_after)}
                    )

        except Exception as e:
            # Database failure: fail open so legitimate requests are not blocked.
            # Rate limiting is temporarily bypassed but the app stays available.
            _logger.error(
                "Rate limit DB error for %s on %s: %s",
                client_ip, request.url.path, e,
                exc_info=True,
            )

        # Request is allowed
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.settings.RATE_LIMIT_PER_MINUTE - current_count))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response
