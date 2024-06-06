from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery


from app.database.models.users import SessionLocal
from app.database.requests.crud import add_or_update_user, update_user_city
from app.templates.keyboards.inline_buttons import gender_start, city_choose
from app.templates.texts.user import message_command_start

start_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


@start_router.message(CommandStart())
async def start(message: Message):
    await message.answer(text=message_command_start)

    user_id = message.from_user.id

    inline_gender = InlineKeyboardMarkup(inline_keyboard=gender_start)
    await message.answer(text="Выберите ваш пол:", reply_markup=inline_gender)


@start_router.callback_query(F.data.in_({"man_gender", "woman_gender"}))
async def process_gender_selection(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    gender = 'Мужчина' if callback_query.data == 'man_gender' else 'Женщина'

    with SessionManager() as db:
        add_or_update_user(user_id=user_id, gender=gender, db=db)

    city_inline = InlineKeyboardMarkup(inline_keyboard=city_choose)
    await callback_query.message.answer(text="Выберите свой город:", reply_markup=city_inline)


@start_router.callback_query(lambda c: c.data.startswith('city_'))
async def process_city_selection(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    city_data = callback_query.data
    city = city_data.split('_', 1)[1]

    with SessionManager() as db:
        update_user_city(db=db, user_id=user_id, city=city)
