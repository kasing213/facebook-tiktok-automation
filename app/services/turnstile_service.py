# app/services/turnstile_service.py
"""
Cloudflare Turnstile CAPTCHA verification service.

Verifies Turnstile tokens by calling the Cloudflare siteverify API.
Disabled by default (TURNSTILE_ENABLED=False) for dev/testing environments.
"""
import logging
import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

_logger = logging.getLogger("app.services.turnstile")

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile(token: str | None, remote_ip: str | None = None) -> None:
    """
    Verify a Cloudflare Turnstile token.

    Args:
        token: The turnstile response token from the frontend widget.
        remote_ip: Optional client IP for additional validation.

    Raises:
        HTTPException 403: If verification is enabled and the token is missing or invalid.
    """
    settings = get_settings()

    if not settings.TURNSTILE_ENABLED:
        return  # Skip verification in dev/testing

    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CAPTCHA verification required",
        )

    secret = settings.TURNSTILE_SECRET_KEY.get_secret_value()
    if not secret:
        _logger.error("TURNSTILE_SECRET_KEY is not configured but TURNSTILE_ENABLED=True")
        return  # Fail open if misconfigured (don't block users)

    payload = {"secret": secret, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(VERIFY_URL, data=payload)
            result = resp.json()

        if result.get("success"):
            return  # Token is valid

        error_codes = result.get("error-codes", [])
        _logger.warning(
            "Turnstile verification failed: %s (IP: %s)",
            error_codes, remote_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CAPTCHA verification failed. Please try again.",
        )
    except httpx.HTTPError as e:
        _logger.error("Turnstile API request failed: %s", e)
        # Fail open on network errors so users aren't blocked
        return
