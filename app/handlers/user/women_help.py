from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery

from app.database.models.users import async_session_maker
from app.database.requests.crud import get_user_info, delete_user_subscription_details
from app.templates.keyboards.inline_buttons import women_subscribe, is_cancel_sub

women_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = async_session_maker()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()


@women_router.message(F.text == "Отменить подписку")
async def cancel_sub_button(message: Message):
    user_id = message.from_user.id
    try:
        cancel_but = InlineKeyboardMarkup(inline_keyboard=is_cancel_sub)
        await message.answer(text="Точно ли вы хотите отменить подписку?",
                             reply_markup=cancel_but)
    except Exception as e:
        print(f"Error in cancel_sub_button for user_id {user_id}: {e}")


@women_router.callback_query(F.data == "yes_cancel_button")
async def yes_want_cancel_sub(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        async with SessionManager() as db:
            await delete_user_subscription_details(db=db, user_id=user_id)
        await callback_query.message.answer(text="Подписка отменена.")
    except Exception as e:
        print(f"Error in yes_want_cancel_sub for user_id {user_id}: {e}")


@women_router.message(F.text == "Помощь")
async def choose_women_subscribe(message: Message):
    user_id = message.from_user.id
    try:
        await message.answer(text="Возник вопрос?\n\nНапишите: @esc222")
    except Exception as e:
        print(f"Error in choose_women_subscribe for user_id {user_id}: {e}")
