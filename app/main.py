"""Application entrypoint."""

from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.admin.routes import router as admin_router
from app.api.error_handlers import register_exception_handlers
from app.api.routers.public import router as public_router
from app.bot.app import create_bot, create_dispatcher
from app.config import get_settings
from app.core.logging import setup_logging
from app.db.redis import create_redis_client


settings = get_settings()
setup_logging(settings.debug)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""

    redis = create_redis_client()
    bot = create_bot()
    dispatcher = create_dispatcher(redis)
    app.state.redis = redis
    app.state.bot = bot
    app.state.dispatcher = dispatcher
    yield
    await bot.session.close()
    await dispatcher.storage.close()
    await redis.close()


def create_app() -> FastAPI:
    """Build FastAPI application."""

    app = FastAPI(title="Telegram Shop MVP", debug=settings.debug, lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(public_router)
    app.include_router(admin_router)

    @app.post("/telegram/webhook")
    async def telegram_webhook(request: Request) -> JSONResponse:
        """Handle Telegram webhook."""

        payload = await request.json()
        update = Update.model_validate(payload)
        await request.app.state.dispatcher.feed_update(request.app.state.bot, update)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"ok": True})

    return app


app = create_app()
