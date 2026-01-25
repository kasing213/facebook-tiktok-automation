# api-gateway/src/bot/handlers/sales.py
"""Sales report command handlers."""

import logging
from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Command

from src.services.sales_service import sales_service
from src.bot.services.linking import get_user_by_telegram_id
from src.bot.utils.permissions import require_member_or_owner

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("sales"))
async def cmd_sales(message: types.Message):
    """Handle /sales command - show sales menu."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not await require_member_or_owner(user, message):
        return

    # Check if service is connected
    stats = await sales_service.get_stats()
    if stats.get("status") != "connected":
        await message.answer(
            "<b>Sales Reports</b>\n\n"
            "⚠️ Service not connected.\n"
            "Please configure MongoDB connection for audit-sales."
        )
        return

    await message.answer(
        "<b>Sales Commands</b>\n\n"
        "/sales today - Today's sales summary\n"
        "/sales stats - View statistics\n"
    )


@router.message(Command("sales_today"))
async def cmd_sales_today(message: types.Message):
    """Handle /sales_today command."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not await require_member_or_owner(user, message):
        return

    today = datetime.now().strftime("%Y-%m-%d")
    summary = await sales_service.get_daily_summary(today)

    if not summary:
        await message.answer(f"No sales data for {today}")
        return

    await message.answer(
        f"<b>Sales Summary - {today}</b>\n\n"
        f"Total Sales: ${summary.get('total', 0):.2f}\n"
        f"Transactions: {summary.get('count', 0)}\n"
        f"Average: ${summary.get('average', 0):.2f}"
    )


@router.message(Command("sales_stats"))
async def cmd_sales_stats(message: types.Message):
    """Handle /sales_stats command."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not await require_member_or_owner(user, message):
        return

    stats = await sales_service.get_stats()

    await message.answer(
        f"<b>Sales Statistics</b>\n\n"
        f"Total Records: {stats.get('total_records', 0)}\n"
        f"This Month: {stats.get('this_month', 0)}"
    )
