from aiogram import Router, F
from aiogram.types import Message

from app.database.models.users import async_session_maker


women_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = async_session_maker()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()


@women_router.message(F.text == "Помощь")
async def choose_women_subscribe(message: Message):
    user_id = message.from_user.id
    try:
        await message.answer(text="Возник вопрос?\n\nНапишите: @esc222")
    except Exception as e:
        print(f"Error in choose_women_subscribe for user_id {user_id}: {e}")
