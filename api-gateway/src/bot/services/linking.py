# api-gateway/src/bot/services/linking.py
"""User linking service for Telegram account connection."""

import logging
from typing import Dict, Any, Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


async def consume_link_code(
    code: str,
    telegram_user_id: str,
    telegram_username: Optional[str] = None
) -> Dict[str, Any]:
    """
    Consume a link code by calling the core API.

    Args:
        code: The link code from the dashboard
        telegram_user_id: Telegram user ID
        telegram_username: Telegram username (optional)

    Returns:
        Result dict with success status and user info
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.CORE_API_URL}/telegram/verify-code",
                json={
                    "code": code,
                    "telegram_user_id": telegram_user_id,
                    "telegram_username": telegram_username
                },
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": data.get("success", False),
                    "user_id": data.get("user_id"),
                    "tenant_id": data.get("tenant_id"),
                    "username": data.get("username"),
                    "email": data.get("email"),
                    "message": data.get("message", "")
                }
            else:
                logger.error(f"Failed to verify code: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": "Failed to verify link code"
                }

    except httpx.RequestError as e:
        logger.error(f"Request error when verifying code: {e}")
        return {
            "success": False,
            "message": "Connection error. Please try again."
        }
    except Exception as e:
        logger.error(f"Unexpected error when verifying code: {e}")
        return {
            "success": False,
            "message": "An unexpected error occurred"
        }


async def get_user_by_telegram_id(telegram_user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user info by Telegram ID from the core API.

    Args:
        telegram_user_id: Telegram user ID

    Returns:
        User info dict or None if not found
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.CORE_API_URL}/telegram/user/{telegram_user_id}",
                timeout=10.0
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.error(f"Failed to get user: {response.status_code}")
                return None

    except Exception as e:
        logger.error(f"Error getting user by Telegram ID: {e}")
        return None
