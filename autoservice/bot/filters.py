"""Custom aiogram filters for role-based handler matching."""

from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message


class RoleFilter(BaseFilter):
    """Filter that checks the db_user role injected by AuthMiddleware."""

    role: Union[str, list]

    async def __call__(self, message: Message, db_user: dict = None) -> bool:
        if not isinstance(db_user, dict):
            return False
        allowed = {self.role} if isinstance(self.role, str) else set(self.role)
        return db_user.get("role") in allowed
