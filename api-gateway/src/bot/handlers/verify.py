# api-gateway/src/bot/handlers/verify.py
"""Screenshot verification command handlers."""

import logging
from aiogram import Router, types
from aiogram.filters import Command

from src.services.screenshot_service import screenshot_service
from src.bot.services.linking import get_user_by_telegram_id
from src.bot.utils.permissions import require_member_or_owner

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("verify"))
async def cmd_verify(message: types.Message):
    """Handle /verify command - show verification menu."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not await require_member_or_owner(user, message):
        return

    # Check if service is connected
    stats = await screenshot_service.get_stats()
    if stats.get("status") != "connected":
        await message.answer(
            "<b>Screenshot Verifier</b>\n\n"
            "⚠️ Service not connected.\n"
            "Please configure MongoDB connection for scriptclient."
        )
        return

    await message.answer(
        "<b>Screenshot Verification Commands</b>\n\n"
        "/verify pending - List pending screenshots\n"
        "/verify stats - View statistics\n"
    )


@router.message(Command("verify_pending"))
async def cmd_verify_pending(message: types.Message):
    """Handle /verify_pending command."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not await require_member_or_owner(user, message):
        return

    pending = await screenshot_service.get_pending_screenshots(limit=10)

    if not pending:
        await message.answer("No pending screenshots.")
        return

    lines = ["<b>Pending Screenshots</b>\n"]
    for item in pending[:10]:
        sc_id = str(item.get("_id", "N/A"))[-8:]
        name = item.get("name", "Unknown")
        lines.append(f"• <code>{sc_id}</code> - {name}")

    await message.answer("\n".join(lines))


@router.message(Command("verify_stats"))
async def cmd_verify_stats(message: types.Message):
    """Handle /verify_stats command."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not await require_member_or_owner(user, message):
        return

    stats = await screenshot_service.get_stats()

    await message.answer(
        f"<b>Screenshot Statistics</b>\n\n"
        f"Total Screenshots: {stats.get('total', 0)}\n"
        f"Verified: {stats.get('verified', 0)}\n"
        f"Pending: {stats.get('pending', 0)}"
    )
