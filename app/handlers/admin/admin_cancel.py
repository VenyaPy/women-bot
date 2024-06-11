from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    CallbackQuery, InlineKeyboardButton
)

from app.database.models.users import SessionLocal
from app.database.requests.crud import get_users_with_active_subscription, get_female_users, get_male_users, \
    get_all_user_ids
from app.filters.chat_types import IsAdmin
from app.templates.keyboards.inline_buttons import users_of_mailing, is_check_post, send_or_delete_mail


class SessionManager:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


admin_cancel_router = Router()
admin_cancel_router.message.filter(IsAdmin())
admin_cancel_router.callback_query.filter(IsAdmin())


@admin_cancel_router.message(F.text.lower() == "Отключить подписку")
async def cancel_sub_menu(message: Message, state: FSMContext):
    await message.answer(text="Введите ID пользователя для отключения подписки")