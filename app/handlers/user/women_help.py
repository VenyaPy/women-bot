from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, Message


from app.database.models.users import SessionLocal
from app.database.requests.crud import get_user_info
from app.templates.keyboards.inline_buttons import women_subscribe


women_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


@women_router.message(F.text == "Помощь")
async def choose_women_subscribe(message: Message):
    await message.answer(text="Возник вопрос? Напишите: @esc222")


