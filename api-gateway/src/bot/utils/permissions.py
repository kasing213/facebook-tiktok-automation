# api-gateway/src/bot/utils/permissions.py
"""
Bot command permission helpers.

Provides role-based access control for Telegram bot commands.
These helpers enforce tenant-level permissions based on user roles.

Role hierarchy:
- admin (owner): Full access to all commands
- user (member): Access to operational commands (invoices, sales, etc.)
- viewer: Read-only access - blocked from most commands

SECURITY: These checks prevent:
1. Viewers accessing sensitive business data via Telegram
2. Members executing owner-only commands like /register_client
3. Unlinked users accessing any commands
"""

from typing import Optional
from aiogram import types


async def require_member_or_owner(user: Optional[dict], message: types.Message) -> bool:
    """
    Check if user has member or owner role.

    Use this for commands that require operational access:
    - /status, /invoice, /sales, /verify, /promo, /ocr, /my_clients

    Args:
        user: User dict from get_user_by_telegram_id(), or None if not linked
        message: Telegram message to reply with error if permission denied

    Returns:
        True if user has permission, False otherwise (error message already sent)
    """
    if not user:
        await message.answer(
            "You need to link your Telegram account first.\n"
            "Go to the dashboard \u2192 Integrations \u2192 Telegram to connect."
        )
        return False

    if user.get("role") == "viewer":
        await message.answer(
            "\u274c You don't have permission for this command.\n"
            "Contact your admin to upgrade your access level."
        )
        return False

    return True


async def require_owner(user: Optional[dict], message: types.Message) -> bool:
    """
    Check if user has owner (admin) role.

    Use this for commands that require tenant ownership:
    - /register_client (creates customer registrations)
    - Any command that modifies tenant configuration

    Args:
        user: User dict from get_user_by_telegram_id(), or None if not linked
        message: Telegram message to reply with error if permission denied

    Returns:
        True if user has permission, False otherwise (error message already sent)
    """
    if not user:
        await message.answer(
            "You need to link your Telegram account first.\n"
            "Go to the dashboard \u2192 Integrations \u2192 Telegram to connect."
        )
        return False

    if user.get("role") != "admin":
        await message.answer(
            "\u274c Only the tenant owner can use this command.\n"
            "Contact your admin if you need access."
        )
        return False

    return True


async def require_linked(user: Optional[dict], message: types.Message) -> bool:
    """
    Check if user is linked (any role is acceptable).

    Use this for read-only or informational commands where even viewers are allowed.

    Args:
        user: User dict from get_user_by_telegram_id(), or None if not linked
        message: Telegram message to reply with error if not linked

    Returns:
        True if user is linked, False otherwise (error message already sent)
    """
    if not user:
        await message.answer(
            "You need to link your Telegram account first.\n"
            "Go to the dashboard \u2192 Integrations \u2192 Telegram to connect."
        )
        return False

    return True
