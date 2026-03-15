from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery


class RoleFilter(Filter):
    def __init__(self, role: str) -> None:
        self.role = role

    async def __call__(self, event: Message | CallbackQuery, db_user: dict) -> bool:
        if not isinstance(db_user, dict):
            return False
        return db_user.get("role") == self.role
