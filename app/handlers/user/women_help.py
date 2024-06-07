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


@women_router.message(F.text == "Добавить анкету")
async def add_questionnaire(message: Message):
    user_id = message.from_user.id
    with SessionManager() as db:
        info = get_user_info(db=db, user_id=user_id)

    sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)

    if not info.subscription_type:
        await message.answer(text="Чтобы воспользоваться этой функцией необходимо оформить подписку:",
                             reply_markup=sub_inline)
    else:
        await message.answer(text="У вас уже есть подписка. Продолжайте добавлять анкету.")


