"""Custom aiogram filters for role-based handler matching."""

from aiogram.filters import BaseFilter
from aiogram.types import Message


class RoleFilter(BaseFilter):
    """Filter that checks the db_user role injected by AuthMiddleware."""

    def __init__(self, *roles: str):
        self.roles = set(roles)

    async def __call__(self, message: Message, db_user: dict = None) -> bool:
        if not isinstance(db_user, dict):
            return False
        return db_user.get("role") in self.roles
