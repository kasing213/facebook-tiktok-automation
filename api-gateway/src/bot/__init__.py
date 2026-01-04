# api-gateway/src/bot/__init__.py
"""Telegram bot module."""

import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from src.config import settings
from src.bot.handlers import start, status, invoice, verify, sales, promo, help_cmd

logger = logging.getLogger(__name__)

# Create bot and dispatcher
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Register handlers
dp.include_router(start.router)
dp.include_router(status.router)
dp.include_router(invoice.router)
dp.include_router(verify.router)
dp.include_router(sales.router)
dp.include_router(promo.router)
dp.include_router(help_cmd.router)


def create_bot() -> tuple[Bot, Dispatcher]:
    """Create and configure the Telegram bot."""
    return bot, dp


async def run_bot():
    """Run the Telegram bot polling."""
    logger.info("Starting Telegram bot polling...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise
