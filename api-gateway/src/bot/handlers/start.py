# api-gateway/src/bot/handlers/start.py
"""Start command handler with account linking."""

import logging
from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject

from src.bot.services.linking import consume_link_code, get_user_by_telegram_id

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart(deep_link=True))
async def cmd_start_with_code(message: types.Message, command: CommandObject):
    """Handle /start with link code (deep link)."""
    code = command.args

    if not code:
        await cmd_start(message)
        return

    logger.info(f"Link code received: {code} from user {message.from_user.id}")

    # Try to consume the link code
    result = await consume_link_code(
        code=code,
        telegram_user_id=str(message.from_user.id),
        telegram_username=message.from_user.username
    )

    if result.get("success"):
        await message.answer(f"""
<b>Telegram Connected Successfully!</b>

Your Telegram account is now linked to the dashboard.

<b>Account Details:</b>
Username: {result.get('username', 'N/A')}
Email: {result.get('email', 'N/A')}

<b>Available Commands:</b>
/status - View all systems status
/invoice - Invoice operations
/verify - Screenshot verification
/sales - Sales reports
/promo - Promotion status
/help - Show all commands
        """.strip())
    else:
        await message.answer(f"""
<b>Link Failed</b>

{result.get('message', 'Invalid or expired code.')}

Please generate a new link code from the dashboard and try again.
        """.strip())


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Handle /start without code."""
    telegram_id = str(message.from_user.id)

    # Check if user is already linked
    user = await get_user_by_telegram_id(telegram_id)

    if user:
        await message.answer(f"""
<b>Welcome back!</b>

Your Telegram account is linked to:
Username: {user.get('username', 'N/A')}
Email: {user.get('email', 'N/A')}

<b>Commands:</b>
/status - View all systems status
/invoice - Invoice operations
/verify - Screenshot verification
/sales - Sales reports
/promo - Promotion status
/help - Show all commands
        """.strip())
    else:
        await message.answer("""
<b>Welcome to Facebook Automation Bot!</b>

This bot allows you to interact with the Facebook Automation platform.

<b>To get started:</b>
1. Log in to your dashboard
2. Go to Integrations → Telegram
3. Click "Connect Telegram"
4. Send the link code here

<b>Or use the deep link:</b>
Click the "Connect" button in your dashboard - it will open this chat automatically.
        """.strip())
