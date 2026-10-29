from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.config import ADMIN_ID


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return ADMIN_ID is not None and message.from_user.id == ADMIN_ID