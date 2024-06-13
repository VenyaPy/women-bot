from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery

import re
from aiogram import types

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.database.models.users import async_session_maker
from app.database.requests.crud import get_user_info, send_women_review
from app.templates.keyboards.inline_buttons import women_subscribe, positive_or_negative, send_or_delete_review

women_review_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = async_session_maker()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()


class Review(StatesGroup):
    type = State()
    number = State()
    text = State()


@women_review_router.callback_query(F.data == "want_to_add_review")
async def add_review_callback(callback_query: CallbackQuery, state: FSMContext):
    try:
        user_id = callback_query.from_user.id
        async with SessionManager() as db:
            info = await get_user_info(db=db, user_id=user_id)

        sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)

        if info.subscription_type not in ["Проверка", "Проверка + Анкета"]:
            await callback_query.message.answer(text="Чтобы воспользоваться этой функцией необходимо оформить подписку (автоматически продлевается каждый месяц):",
                                                reply_markup=sub_inline)
            return

        await state.set_state(Review.type)
        pos_or_neg = InlineKeyboardMarkup(inline_keyboard=positive_or_negative)
        await callback_query.message.answer(text="Какой отзыв вы хотите добавить?", reply_markup=pos_or_neg)
    except Exception as e:
        await callback_query.message.answer("Произошла ошибка при добавлении отзыва. Попробуйте еще раз.")
        print(f"Error in add_review: {e}")


@women_review_router.message(F.text == "Добавить отзыв")
async def add_review(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        async with SessionManager() as db:
            info = await get_user_info(db=db, user_id=user_id)

        sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)
        print("Subscription status:", info.subscription_status)

        if info.subscription_type not in ["Проверка", "Проверка + Анкета"]:
            await message.answer(text="Чтобы воспользоваться этой функцией необходимо оформить подписку (автоматически продлевается каждый месяц):",
                                 reply_markup=sub_inline)
            return

        await state.set_state(Review.type)
        pos_or_neg = InlineKeyboardMarkup(inline_keyboard=positive_or_negative)
        await message.answer(text="Какой отзыв вы хотите добавить?", reply_markup=pos_or_neg)
    except Exception as e:
        await message.answer("Произошла ошибка при добавлении отзыва. Попробуйте еще раз.")
        print(f"Error in add_review: {e}")



@women_review_router.callback_query(F.data == "review_positive")
async def review_positive(callback_query: CallbackQuery, state: FSMContext):
    try:
        await state.update_data(type='positive')
        await callback_query.message.answer("Введите номер телефона в формате: 8 *** *** ** **")
        await state.set_state(Review.number)
    except Exception as e:
        await callback_query.message.answer("Произошла ошибка при выборе положительного отзыва.")
        print(f"Error in review_positive: {e}")


@women_review_router.callback_query(F.data == "review_negative")
async def review_negative(callback_query: CallbackQuery, state: FSMContext):
    try:
        await state.update_data(type='negative')
        await callback_query.message.answer("Введите номер телефона в формате: 8 *** *** ** **")
        await state.set_state(Review.number)
    except Exception as e:
        await callback_query.message.answer("Произошла ошибка при выборе отрицательного отзыва.")
        print(f"Error in review_negative: {e}")


def format_phone_number(phone_number: str) -> str:
    digits = re.sub(r'\D', '', phone_number)
    if len(digits) == 11 and digits.startswith('7'):
        digits = '8' + digits[1:]
    elif len(digits) == 10:
        digits = '8' + digits
    elif len(digits) != 11 or not digits.startswith('8'):
        return "Ошибка! Введите номер в верном формате."
    formatted_number = f'{digits[0]} {digits[1:4]} {digits[4:7]} {digits[7:9]} {digits[9:]}'
    return formatted_number


@women_review_router.message(Review.number)
async def take_number(message: Message, state: FSMContext):
    phone_number = message.text
    formatted_number = format_phone_number(phone_number)

    if formatted_number.startswith("Ошибка"):
        await message.answer(text=formatted_number)
        await message.answer(text="Введите номер телефона в формате: 8 *** *** ** **")
    else:
        await state.update_data(number=formatted_number)
        await message.answer(text=f"Номер телефона принят: {formatted_number}")
        await state.set_state(Review.text)
        await message.answer(text="Введите текст отзыва:")


@women_review_router.message(Review.text)
async def add_text(message: Message, state: FSMContext):
    try:
        await state.update_data(text=message.text)
        inline_send_or_delete_review = InlineKeyboardMarkup(inline_keyboard=send_or_delete_review)
        await message.answer(text="Отправить отзыв или отменить?", reply_markup=inline_send_or_delete_review)
    except Exception as e:
        await message.answer("Произошла ошибка при добавлении текста отзыва.")
        print(f"Error in add_text: {e}")


@women_review_router.callback_query(F.data == 'send_review_to_bd')
async def send_done_review(callback: CallbackQuery, state: FSMContext):
    try:
        if F.data == "send_review_to_bd":
            data = await state.get_data()
            user_id = callback.message.from_user.id
            type = data.get("type", "")
            number = data.get("number", "")
            text = data.get("text", "")
            async with SessionManager() as db:
                await send_women_review(db=db, user_id=user_id, type=type, number=number, text=text)
            await callback.message.answer("Отзыв отправлен. Спасибо!")
            await state.clear()
    except Exception as e:
        await callback.message.answer("Произошла ошибка при отправке отзыва.")
        print(f"Error in send_done_review: {e}")


@women_review_router.callback_query(F.data == "cancel_review")
async def cancel_last_review(callback_query: CallbackQuery, state: FSMContext):
    try:
        if F.data == "cancel_review":
            await state.clear()
            await callback_query.message.answer(text="Отзыв отменен")
    except Exception as e:
        await callback_query.message.answer("Произошла ошибка при отмене отзыва.")
        print(f"Error in cancel_last_review: {e}")


