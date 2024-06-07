from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, Message

from app.database.models.users import SessionLocal
from app.templates.keyboards.inline_buttons import women_subscribe

men_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


@men_router.message()
async def men_canvass():
    pass