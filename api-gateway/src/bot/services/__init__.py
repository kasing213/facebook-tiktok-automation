# api-gateway/src/bot/services/__init__.py
"""Bot services."""

from .linking import consume_link_code, get_user_by_telegram_id

__all__ = [
    "consume_link_code",
    "get_user_by_telegram_id",
]
