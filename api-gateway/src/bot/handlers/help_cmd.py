# api-gateway/src/bot/handlers/help_cmd.py
"""Help command handler."""

import logging
from aiogram import Router, types
from aiogram.filters import Command

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command - show all available commands."""
    await message.answer("""
<b>Facebook Automation Bot Commands</b>

<b>General</b>
/start - Start the bot / Link account
/status - View all systems status
/help - Show this help message

<b>Invoice Generator</b>
/invoice - Invoice menu
/invoice_list - List recent invoices
/invoice_stats - Invoice statistics

<b>Screenshot Verifier</b>
/verify - Verification menu
/verify_pending - List pending screenshots
/verify_stats - Verification statistics

<b>Sales Reports</b>
/sales - Sales menu
/sales_today - Today's sales summary
/sales_stats - Sales statistics

<b>Promotions</b>
/promo - Promotion menu
/promo_status - Current promotion status
/promo_chats - Registered chats

<b>Inventory Management</b>
/inventory - View current stock levels
/lowstock - Check items running low

<i>Need help? Contact your administrator.</i>
    """.strip())
