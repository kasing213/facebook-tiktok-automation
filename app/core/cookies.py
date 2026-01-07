# app/core/cookies.py
"""
Cookie utilities for secure refresh token management.
"""
from fastapi import Response
from app.core.config import get_settings
from app.core.security import REFRESH_TOKEN_EXPIRE_DAYS


def set_refresh_token_cookie(response: Response, token: str) -> None:
    """
    Set the refresh token as an httpOnly cookie.

    Args:
        response: FastAPI Response object
        token: The raw refresh token value
    """
    settings = get_settings()
    max_age = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # Convert days to seconds

    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
        samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
        domain=settings.REFRESH_TOKEN_COOKIE_DOMAIN,
        path="/auth",  # Restrict to auth endpoints only
    )


def clear_refresh_token_cookie(response: Response) -> None:
    """
    Clear the refresh token cookie.

    Args:
        response: FastAPI Response object
    """
    settings = get_settings()

    response.delete_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        path="/auth",
        domain=settings.REFRESH_TOKEN_COOKIE_DOMAIN,
        secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
        samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
    )


def get_refresh_token_cookie_name() -> str:
    """Get the configured refresh token cookie name."""
    settings = get_settings()
    return settings.REFRESH_TOKEN_COOKIE_NAME
