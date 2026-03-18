"""Bot factory."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from app.bot.handlers.shop import router as shop_router
from app.config import get_settings


settings = get_settings()


def create_bot() -> Bot:
    """Create Telegram bot."""

    return Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))


def create_dispatcher(redis: Redis) -> Dispatcher:
    """Create aiogram dispatcher."""

    storage = RedisStorage(redis=redis)
    dispatcher = Dispatcher(storage=storage)
    dispatcher.include_router(shop_router)
    dispatcher["redis"] = redis
    return dispatcher
