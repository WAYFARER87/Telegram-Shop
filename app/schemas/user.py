"""User schemas."""

from pydantic import BaseModel

from app.schemas.common import TimestampSchema


class UserRead(TimestampSchema):
    """User read schema."""

    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


class TelegramUserPayload(BaseModel):
    """Telegram user data payload."""

    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
