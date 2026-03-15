from typing import Any
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery


class RoleFilter(Filter):
    def __init__(self, role: str) -> None:
        self.role = role

    async def __call__(self, event: Message | CallbackQuery, **kwargs: Any) -> bool:
        db_user = kwargs.get("db_user") or {}
        return db_user.get("role") == self.role
