# api-gateway/src/bot/handlers/status.py
"""Status command handler."""

import logging
from aiogram import Router, types
from aiogram.filters import Command

from src.services.invoice_service import invoice_service
from src.services.screenshot_service import screenshot_service
from src.services.sales_service import sales_service
from src.services.promo_service import promo_service
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

    # Check PostgreSQL schema connections
    services_status = []

    try:
        invoice_stats = await invoice_service.get_stats()
        services_status.append(("Invoice Generator", invoice_stats.get("status") == "connected"))
    except Exception:
        services_status.append(("Invoice Generator", False))

    try:
        screenshot_stats = await screenshot_service.get_stats()
        services_status.append(("Screenshot Verifier", screenshot_stats.get("status") == "connected"))
    except Exception:
        services_status.append(("Screenshot Verifier", False))

    try:
        sales_stats = await sales_service.get_stats()
        services_status.append(("Audit Sales", sales_stats.get("status") == "connected"))
    except Exception:
        services_status.append(("Audit Sales", False))

    try:
        promo_stats = await promo_service.get_stats()
        services_status.append(("Ads Alert", promo_stats.get("status") == "connected"))
    except Exception:
        services_status.append(("Ads Alert", False))

    # Build status message
    status_lines = ["<b>System Status</b>\n"]

    for name, connected in services_status:
        icon = "🟢" if connected else "🔴"
        status_text = "Connected" if connected else "Not configured"
        status_lines.append(f"{icon} <b>{name}:</b> {status_text}")

    status_lines.append("\n<i>Use /help to see available commands</i>")

    await message.answer("\n".join(status_lines))
