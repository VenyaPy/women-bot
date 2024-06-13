from aiogram.filters import Filter
from aiogram import Bot, types

from app.database.models.users import async_session_maker
from config import ADMINS


class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = async_session_maker()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()


class IsAdmin(Filter):
    async def __call__(self, message: types.Message, bot: Bot):
        try:
            is_admin = message.from_user.id in ADMINS
        except Exception as e:
            print(f"Ошибка при доступе к базе данных: {e}")
            is_admin = False
        return is_admin