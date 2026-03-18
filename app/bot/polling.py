"""Long polling entrypoint for Telegram bot."""

import asyncio
import logging

from app.bot.app import create_bot, create_dispatcher
from app.config import get_settings
from app.core.logging import setup_logging
from app.db.redis import create_redis_client


settings = get_settings()
setup_logging(settings.debug)
logger = logging.getLogger(__name__)


async def run_polling() -> None:
    """Start Telegram bot in long polling mode."""

    redis = create_redis_client()
    bot = create_bot()
    dispatcher = create_dispatcher(redis)
    try:
        # Polling and webhook cannot be used together reliably.
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Starting bot polling")
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await dispatcher.storage.close()
        await redis.close()


if __name__ == "__main__":
    asyncio.run(run_polling())
