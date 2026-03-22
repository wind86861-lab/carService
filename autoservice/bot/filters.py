"""Custom aiogram filters for role-based handler matching."""

import logging
from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message

logger = logging.getLogger(__name__)


class RoleFilter(BaseFilter):
    """Filter that checks the db_user role injected by AuthMiddleware."""

    def __init__(self, role: Union[str, list[str], set[str]]):
        if isinstance(role, str):
            self.roles = {role}
        else:
            self.roles = set(role)

    async def __call__(self, message: Message, db_user: dict = None) -> bool:
        user_role = db_user.get("role") if isinstance(db_user, dict) else None
        result = user_role in self.roles
        logger.info("RoleFilter check: user_role=%s, allowed=%s, result=%s", user_role, self.roles, result)
        if not isinstance(db_user, dict):
            return False
        return result
