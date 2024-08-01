from aiogram import F, Router
from aiogram.types import Message

from app.database.models.users import async_session_maker
from app.database.requests.crud import (count_female_users_with_no_subscription,
                                        count_male_users)
from app.filters.chat_types import IsAdmin


class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = async_session_maker()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()


admin_stat = Router()
admin_stat.message.filter(IsAdmin())
admin_stat.callback_query.filter(IsAdmin())


@admin_stat.message(F.text.lower() == "статистика")
async def get_stat_for_users(message: Message):
    """
    Функция отображает количество мужчин и женщин без подписки
    """
    try:
        async with SessionManager() as db:
            count_female = await count_female_users_with_no_subscription(db=db)

        async with SessionManager() as db:
            count_male = await count_male_users(db=db)

        await message.answer(f"Количество мужчин: {count_male}\n"
                             f"Количество женщин без подписки: {count_female}")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
