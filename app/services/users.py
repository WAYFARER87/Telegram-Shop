"""User services."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.users import UserRepository


logger = logging.getLogger(__name__)


class UserService:
    """User business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def register_telegram_user(
        self,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        phone: str | None = None,
    ):
        """Create or update telegram user."""

        user = await self.users.create_or_update(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )
        await self.session.commit()
        await self.session.refresh(user)
        logger.info("User registered telegram_id=%s user_id=%s", telegram_id, user.id)
        return user
