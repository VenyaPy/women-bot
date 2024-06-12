from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from app.database.models.users import SessionLocal
from app.database.requests.crud import get_users_with_active_subscription, get_female_users, get_male_users, \
    get_all_user_ids, get_user_info, delete_user_subscription_details
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



class CancelSubscriptionForm(StatesGroup):
    ask_user_id = State()


admin_cancel_router = Router()
admin_cancel_router.message.filter(IsAdmin())
admin_cancel_router.callback_query.filter(IsAdmin())


@admin_cancel_router.message(F.text.lower() == "отключить подписку")
async def cancel_sub_menu(message: Message, state: FSMContext):
    await state.set_state(CancelSubscriptionForm.ask_user_id)
    await message.answer(text="Введите ID пользователя для отключения подписки")


@admin_cancel_router.message(CancelSubscriptionForm.ask_user_id)
async def process_user_id(message: Message, state: FSMContext):
    user_id = message.text.strip()

    try:
        user_id = int(user_id)
    except ValueError:
        await message.answer("Пожалуйста, введите правильный числовой ID пользователя.")
        return

    try:
        with SessionManager() as db:
            user_info = get_user_info(db, user_id)
            if user_info:
                user = delete_user_subscription_details(db, user_id)
                if user:
                    await message.answer(f"Подписка для пользователя с ID {user_id} успешно отключена.\n\n"
                                         f"customer_key: {user_info.customer_key}\n"
                                         f"payment_id: {user_info.payment_id}")
                else:
                    await message.answer(f"Пользователь с ID {user_id} не найден.")
            else:
                await message.answer(f"Пользователь с ID {user_id} не найден.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
    finally:
        await state.clear()
