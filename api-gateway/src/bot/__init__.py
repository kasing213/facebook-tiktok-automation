# api-gateway/src/bot/__init__.py
"""Telegram bot module."""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Lazy-loaded bot and dispatcher
_bot = None
_dp = None


def _init_bot():
    """Initialize bot and dispatcher lazily."""
    global _bot, _dp

    if _bot is not None:
        return _bot, _dp

    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from src.config import settings
    from src.bot.handlers import start, status, invoice, verify, sales, promo, help_cmd, ocr, client, inventory

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set - bot will not start")
        return None, None

    _bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    _dp = Dispatcher()

    # Register handlers
    _dp.include_router(start.router)
    _dp.include_router(status.router)
    _dp.include_router(invoice.router)
    _dp.include_router(verify.router)
    _dp.include_router(sales.router)
    _dp.include_router(promo.router)
    _dp.include_router(help_cmd.router)
    _dp.include_router(ocr.router)
    _dp.include_router(client.router)  # Client registration and payment verification
    _dp.include_router(inventory.router)  # Inventory management commands

    return _bot, _dp


def create_bot():
    """Create and configure the Telegram bot."""
    return _init_bot()


async def run_bot():
    """Run the Telegram bot polling."""
    import asyncio

    try:
        bot, dp = _init_bot()
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}", exc_info=True)
        # Keep running to not crash the app
        while True:
            await asyncio.sleep(3600)
        return

    if bot is None or dp is None:
        logger.warning("Bot not initialized - skipping polling")
        # Keep running to not crash the app
        while True:
            await asyncio.sleep(3600)
        return

    logger.info("Starting Telegram bot polling...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot polling error: {e}", exc_info=True)
        raise
