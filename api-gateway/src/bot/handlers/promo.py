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

    # Check if service is connected
    stats = await promo_service.get_stats()
    if stats.get("status") != "connected":
        await message.answer(
            "<b>Promotions</b>\n\n"
            "⚠️ Service not connected.\n"
            "Please configure MongoDB connection for ads-alert."
        )
        return

    await message.answer(
        "<b>Promotion Commands</b>\n\n"
        "/promo status - Current promotion status\n"
        "/promo chats - Registered chats\n"
    )


@router.message(Command("promo_status"))
async def cmd_promo_status(message: types.Message):
    """Handle /promo_status command."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer("Please link your account first.")
        return

    status = await promo_service.get_current_status()

    if not status:
        await message.answer("No promotion status available.")
        return

    await message.answer(
        f"<b>Promotion Status</b>\n\n"
        f"Active: {'Yes' if status.get('active') else 'No'}\n"
        f"Last Sent: {status.get('last_sent', 'N/A')}\n"
        f"Next Scheduled: {status.get('next_scheduled', 'N/A')}"
    )


@router.message(Command("promo_chats"))
async def cmd_promo_chats(message: types.Message):
    """Handle /promo_chats command."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer("Please link your account first.")
        return

    chats = await promo_service.get_registered_chats()

    if not chats:
        await message.answer("No registered chats.")
        return

    lines = ["<b>Registered Chats</b>\n"]
    for chat in chats[:20]:
        name = chat.get("name", "Unknown")
        chat_id = chat.get("chat_id", "N/A")
        lines.append(f"• {name} (<code>{chat_id}</code>)")

    await message.answer("\n".join(lines))
