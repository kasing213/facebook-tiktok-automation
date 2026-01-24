# api-gateway/src/bot/handlers/promo.py
"""Promotion/Ads Alert command handlers."""

import logging
from aiogram import Router, types
from aiogram.filters import Command

from src.services.promo_service import promo_service
from src.bot.services.linking import get_user_by_telegram_id

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("promo"))
async def cmd_promo(message: types.Message):
    """Handle /promo command - show promo menu."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer(
            "You need to link your Telegram account first.\n"
            "Go to the dashboard → Integrations → Telegram to connect."
        )
        return

    # Get tenant_id for tenant-isolated queries
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        await message.answer("Account configuration error. Please re-link your Telegram account.")
        return

    # Check if service is connected
    stats = await promo_service.get_stats(tenant_id)
    if stats.get("status") != "connected":
        await message.answer(
            "<b>Promotions</b>\n\n"
            "Service not connected.\n"
            "Please configure the database connection for ads-alert.",
            parse_mode="HTML"
        )
        return

    # Show stats summary and commands
    chats_count = stats.get("registered_chats", 0)
    promos_count = stats.get("promotions", 0)

    await message.answer(
        "<b>Promotions</b>\n\n"
        f"Registered Chats: <b>{chats_count}</b>\n"
        f"Total Promotions: <b>{promos_count}</b>\n\n"
        "<b>Commands</b>\n"
        "/promo_status - Current promotion status\n"
        "/promo_chats - List registered chats\n\n"
        "<i>Manage promotions from the dashboard.</i>",
        parse_mode="HTML"
    )


@router.message(Command("promo_status"))
async def cmd_promo_status(message: types.Message):
    """Handle /promo_status command."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer("Please link your account first.")
        return

    # Get tenant_id for tenant-isolated queries
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        await message.answer("Account configuration error. Please re-link your Telegram account.")
        return

    status = await promo_service.get_current_status(tenant_id)

    if not status:
        await message.answer(
            "<b>Promotion Status</b>\n\n"
            "No active promotion configured.\n\n"
            "<i>Create promotions from the dashboard.</i>",
            parse_mode="HTML"
        )
        return

    # Format status with indicators
    is_active = status.get("active", False)
    status_icon = "Active" if is_active else "Inactive"
    status_indicator = "ON" if is_active else "OFF"

    last_sent = status.get("last_sent", "Never")
    next_scheduled = status.get("next_scheduled", "Not scheduled")

    await message.answer(
        f"<b>Promotion Status</b>\n\n"
        f"Status: <b>{status_indicator}</b> ({status_icon})\n"
        f"Last Sent: {last_sent}\n"
        f"Next Scheduled: {next_scheduled}",
        parse_mode="HTML"
    )


@router.message(Command("promo_chats"))
async def cmd_promo_chats(message: types.Message):
    """Handle /promo_chats command."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer("Please link your account first.")
        return

    # Get tenant_id for tenant-isolated queries
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        await message.answer("Account configuration error. Please re-link your Telegram account.")
        return

    chats = await promo_service.get_registered_chats(tenant_id)

    if not chats:
        await message.answer(
            "<b>Registered Chats</b>\n\n"
            "No chats registered yet.\n\n"
            "<i>Add chats from the dashboard.</i>",
            parse_mode="HTML"
        )
        return

    # Count active vs inactive
    active_count = sum(1 for c in chats if c.get("is_active", False))
    total_count = len(chats)

    lines = [
        f"<b>Registered Chats</b>\n",
        f"Total: <b>{total_count}</b> ({active_count} active)\n"
    ]

    for chat in chats[:15]:
        name = chat.get("chat_name") or chat.get("name") or "Unknown"
        chat_id = chat.get("chat_id", "N/A")
        platform = chat.get("platform", "telegram")
        is_active = chat.get("is_active", False)

        # Platform indicator
        platform_label = platform.capitalize() if platform else "Telegram"

        # Active indicator
        active_mark = "" if is_active else " [inactive]"

        lines.append(f"  {platform_label}: <b>{name}</b>{active_mark}")

    if total_count > 15:
        lines.append(f"\n<i>...and {total_count - 15} more</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")
