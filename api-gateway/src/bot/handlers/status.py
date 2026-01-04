# api-gateway/src/bot/handlers/status.py
"""Status command handler."""

import logging
from aiogram import Router, types
from aiogram.filters import Command

from src.db import mongo_manager
from src.bot.services.linking import get_user_by_telegram_id

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("status"))
async def cmd_status(message: types.Message):
    """Handle /status command - show all systems status."""
    telegram_id = str(message.from_user.id)

    # Check if user is linked
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer(
            "You need to link your Telegram account first.\n"
            "Go to the dashboard → Integrations → Telegram to connect."
        )
        return

    # Check MongoDB connections
    mongo_status = await mongo_manager.health_check()

    # Build status message
    status_lines = ["<b>System Status</b>\n"]

    # MongoDB services
    services = [
        ("Invoice Generator", "invoice", mongo_status.get("invoice", False)),
        ("Screenshot Verifier", "scriptclient", mongo_status.get("scriptclient", False)),
        ("Audit Sales", "audit_sales", mongo_status.get("audit_sales", False)),
        ("Ads Alert", "ads_alert", mongo_status.get("ads_alert", False)),
    ]

    for name, key, connected in services:
        icon = "🟢" if connected else "🔴"
        status_text = "Connected" if connected else "Not configured"
        status_lines.append(f"{icon} <b>{name}:</b> {status_text}")

    status_lines.append("\n<i>Use /help to see available commands</i>")

    await message.answer("\n".join(status_lines))
