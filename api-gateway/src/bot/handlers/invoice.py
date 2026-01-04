# api-gateway/src/bot/handlers/invoice.py
"""Invoice command handlers."""

import logging
from aiogram import Router, types
from aiogram.filters import Command

from src.services.invoice_service import invoice_service
from src.bot.services.linking import get_user_by_telegram_id

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("invoice"))
async def cmd_invoice(message: types.Message):
    """Handle /invoice command - show invoice menu."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer(
            "You need to link your Telegram account first.\n"
            "Go to the dashboard → Integrations → Telegram to connect."
        )
        return

    # Check if service is connected
    stats = await invoice_service.get_stats()
    if stats.get("status") != "connected":
        await message.answer(
            "<b>Invoice Generator</b>\n\n"
            "⚠️ Service not connected.\n"
            "Please configure MongoDB connection for invoice-generator."
        )
        return

    await message.answer(
        "<b>Invoice Commands</b>\n\n"
        "/invoice list - List recent invoices\n"
        "/invoice search <name> - Search customer\n"
        "/invoice stats - View statistics\n"
    )


@router.message(Command("invoice_list"))
async def cmd_invoice_list(message: types.Message):
    """Handle /invoice_list command."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer("Please link your account first.")
        return

    invoices = await invoice_service.get_invoices(limit=10)

    if not invoices:
        await message.answer("No invoices found.")
        return

    lines = ["<b>Recent Invoices</b>\n"]
    for inv in invoices[:10]:
        inv_id = inv.get("invoiceNumber", inv.get("_id", "N/A"))
        customer = inv.get("customerName", "Unknown")
        total = inv.get("total", 0)
        lines.append(f"• <code>{inv_id}</code> - {customer} - ${total:.2f}")

    await message.answer("\n".join(lines))


@router.message(Command("invoice_stats"))
async def cmd_invoice_stats(message: types.Message):
    """Handle /invoice_stats command."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer("Please link your account first.")
        return

    stats = await invoice_service.get_stats()

    await message.answer(
        f"<b>Invoice Statistics</b>\n\n"
        f"Total Customers: {stats.get('customers', 0)}\n"
        f"Total Invoices: {stats.get('invoices', 0)}"
    )
