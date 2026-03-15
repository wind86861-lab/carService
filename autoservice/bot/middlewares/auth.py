from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from bot.config import ADMIN_IDS
from bot.database.models import get_user_by_telegram_id, create_user, update_user_role


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Extract the Telegram user from the event
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user
        else:
            return await handler(event, data)

        if tg_user is None:
            return await handler(event, data)

        # Look up or auto-register the user
        db_user = await get_user_by_telegram_id(tg_user.id)
        if db_user is None:
            db_user = await create_user(
                telegram_id=tg_user.id,
                full_name=tg_user.full_name or "Unknown",
                phone=None,
                role="client",
            )

        # Promote to admin if telegram_id is in ADMIN_IDS
        if tg_user.id in ADMIN_IDS and db_user["role"] != "admin":
            await update_user_role(tg_user.id, "admin")
            db_user = await get_user_by_telegram_id(tg_user.id)

        data["db_user"] = db_user
        return await handler(event, data)
