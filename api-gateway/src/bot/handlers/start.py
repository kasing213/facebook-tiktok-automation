# api-gateway/src/bot/handlers/start.py
"""Start command handler with account linking."""

import logging
from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject

from src.bot.services.linking import consume_link_code, get_user_by_telegram_id
from src.bot.handlers.client import handle_client_registration

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart(deep_link=True))
async def cmd_start_with_code(message: types.Message, command: CommandObject):
    """Handle /start with link code (deep link)."""
    try:
        code = command.args

        if not code:
            await cmd_start(message)
            return

        logger.info(f"Link code received: {code} from user {message.from_user.id}")

        # Check if this is a client registration link
        if code.startswith("client_"):
            client_code = code[7:]  # Remove 'client_' prefix
            handled = await handle_client_registration(message, client_code)
            if handled:
                return
            # If not handled (invalid code), fall through to show error

        # Try to consume the merchant link code
        result = await consume_link_code(
            code=code,
            telegram_user_id=str(message.from_user.id),
            telegram_username=message.from_user.username
        )

        if result.get("success"):
            await message.answer(
                "<b>Telegram Connected Successfully!</b>\n\n"
                "Your Telegram account is now linked to the dashboard.\n\n"
                f"<b>Account Details:</b>\n"
                f"Username: {result.get('username', 'N/A')}\n"
                f"Email: {result.get('email', 'N/A')}\n\n"
                "<b>Available Commands:</b>\n"
                "/register_client - Register a client\n"
                "/my_clients - View your registered clients\n"
                "/verify_invoice - Verify payment screenshot\n"
                "/status - View all systems status\n"
                "/help - Show all commands\n\n"
                "<b>To register your clients for invoice notifications:</b>\n"
                "Use: /register_client Client Name"
            )
        else:
            await message.answer(
                "<b>Link Failed</b>\n\n"
                f"{result.get('message', 'Invalid or expired code.')}\n\n"
                "Please generate a new link code from the dashboard and try again."
            )
    except Exception as e:
        logger.error(f"Error in cmd_start_with_code: {e}", exc_info=True)
        await message.answer(
            "<b>Error</b>\n\nSomething went wrong. Please try again."
        )


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Handle /start without code."""
    try:
        telegram_id = str(message.from_user.id)
        logger.info(f"Processing /start for user {telegram_id}")

        # Check if user is already linked
        user = await get_user_by_telegram_id(telegram_id)
        logger.info(f"User lookup result: {user is not None}")

        if user:
            await message.answer(
                "<b>Welcome back!</b>\n\n"
                "Your Telegram account is linked to:\n"
                f"Username: {user.get('username', 'N/A')}\n"
                f"Email: {user.get('email', 'N/A')}\n\n"
                "<b>Commands:</b>\n"
                "/register_client - Register a client\n"
                "/my_clients - View your registered clients\n"
                "/verify_invoice - Verify payment screenshot\n"
                "/status - View all systems status\n"
                "/help - Show all commands"
            )
        else:
            await message.answer(
                "<b>Welcome to KS Automation Bot!</b>\n\n"
                "This bot allows you to interact with the automation platform.\n\n"
                "<b>To get started:</b>\n"
                "1. Log in to your dashboard\n"
                "2. Go to Integrations - Telegram\n"
                "3. Click Connect Telegram\n"
                "4. Send the link code here\n\n"
                "<b>Or use the deep link:</b>\n"
                "Click the Connect button in your dashboard."
            )
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}", exc_info=True)
        await message.answer(
            "<b>Welcome!</b>\n\nUse /help to see available commands."
        )
