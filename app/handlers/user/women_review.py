from aiogram import Router, F
from aiogram.types import (InlineKeyboardMarkup,
                           Message,
                           CallbackQuery)

import re
from aiogram import types

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.database.models.users import async_session_maker
from app.database.requests.crud import (get_user_info,
                                        send_women_review)
from app.templates.keyboards.inline_buttons import (women_subscribe,
                                                    positive_or_negative,
                                                    send_or_delete_review)

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


@women_review_router.callback_query(F.data.startswith("want_to_add_review_"))
async def add_review_callback(callback_query: CallbackQuery, state: FSMContext):
    """
    Функция добавления отзыва о номере телефона мужчины
    """
    user_id = callback_query.from_user.id

    try:
        user_id = callback_query.from_user.id
        phone_number = callback_query.data[len("want_to_add_review_"):]
        formatted_phone_number = format_phone_number(phone_number)

        await state.update_data(number=formatted_phone_number)

        async with SessionManager() as db:
            info = await get_user_info(db=db, user_id=user_id)

        if info.subscription_type not in ["Проверка", "Проверка + Анкета"]:
            sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)
            await callback_query.message.answer(
                text="Чтобы воспользоваться этой функцией необходимо оформить подписку:",
                reply_markup=sub_inline
            )
            return

        await state.set_state(Review.type)
        pos_or_neg = InlineKeyboardMarkup(inline_keyboard=positive_or_negative)
        await callback_query.message.answer(text="Какой отзыв вы хотите добавить?",
                                            reply_markup=pos_or_neg)
    except Exception as e:
        print(f"Ошибка в add_review_callback для user_id {user_id}: {e}")


@women_review_router.message(F.text == "Добавить отзыв")
async def add_review(message: Message, state: FSMContext):
    """
    Функция обработки кнопки о добавлении отзыва при оформленной подписки
    """
    user_id = message.from_user.id

    try:
        user_id = message.from_user.id
        async with SessionManager() as db:
            info = await get_user_info(db=db, user_id=user_id)

        if info.subscription_type not in ["Проверка", "Проверка + Анкета"]:
            sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)
            await message.answer(
                text="Чтобы воспользоваться этой функцией "
                     "необходимо оформить подписку (автоматически "
                     "продлевается каждый месяц):",
                reply_markup=sub_inline
            )
            return

        await state.set_state(Review.type)
        pos_or_neg = InlineKeyboardMarkup(inline_keyboard=positive_or_negative)
        await message.answer(text="Какой отзыв вы хотите добавить?",
                             reply_markup=pos_or_neg)
    except Exception as e:
        print(f"Ошибка в add_review для user_id {user_id}: {e}")


async def handle_review_type(callback_query: CallbackQuery,
                             state: FSMContext,
                             review_type: str):
    """
    Определение типа отзыва (негативный или позитивный) и перевод на ввод номера телефона
    """
    try:
        await state.update_data(type=review_type)
        data = await state.get_data()
        number = data.get("number")

        if not number:
            await callback_query.message.answer("Введите номер телефона "
                                                "в формате: 8 *** *** ** **")
            await state.set_state(Review.number)
        else:
            await state.set_state(Review.text)
            await callback_query.message.answer(text="Введите текст отзыва:")
    except Exception as e:
        print(f"Ошибка в handle_review_type "
              f"для user_id {callback_query.from_user.id}: {e}")


@women_review_router.callback_query(F.data == "review_positive")
async def review_positive(callback_query: CallbackQuery, state: FSMContext):
    await handle_review_type(callback_query, state, "positive")


@women_review_router.callback_query(F.data == "review_negative")
async def review_negative(callback_query: CallbackQuery, state: FSMContext):
    await handle_review_type(callback_query, state, "negative")


def format_phone_number(phone_number: str) -> str:
    """
    Форматирование номера телефона в формат: 8 *** *** ** **
    """
    try:
        digits = re.sub(r'\D', '', phone_number)

        if len(digits) == 11 and digits.startswith('7'):
            digits = '8' + digits[1:]
        elif len(digits) == 10 and not (digits.startswith('8') or digits.startswith('7')):
            digits = '8' + digits
        elif len(digits) != 11 or not digits.startswith('8'):
            return "Ошибка! Введите номер в верном формате."

        formatted_number = f'{digits[0]} {digits[1:4]} {digits[4:7]} {digits[7:9]} {digits[9:]}'
        return formatted_number
    except Exception as e:
        print(f"Error in format_phone_number: {e}")
        return "Ошибка! Введите номер в верном формате."


@women_review_router.message(Review.number)
async def take_number(message: Message, state: FSMContext):
    """
    Сохранение номера телефона и ожидание текста отзыва
    """
    try:
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
    except Exception as e:
        print(f"Ошибка в take_number для user_id {message.from_user.id}: {e}")


@women_review_router.message(Review.text)
async def add_text(message: Message, state: FSMContext):
    """
    Ожидание текста отзыва и ожидание сохранения
    """
    try:
        await state.update_data(text=message.text)
        inline_send_or_delete_review = InlineKeyboardMarkup(inline_keyboard=send_or_delete_review)
        await message.answer(text="Отправить отзыв или отменить?",
                             reply_markup=inline_send_or_delete_review)
    except Exception as e:
        print(f"Ошибка в add_text для user_id {message.from_user.id}: {e}")


@women_review_router.callback_query(F.data == 'send_review_to_bd')
async def send_done_review(callback: CallbackQuery, state: FSMContext):
    """
    Функция сохранение отзыва в базу данных
    """
    user_id = callback.from_user.id

    try:
        data = await state.get_data()
        user_id = callback.message.from_user.id
        review_type = data.get("type", "")
        number = data.get("number", "")
        text = data.get("text", "")
        async with SessionManager() as db:
            await send_women_review(db=db,
                                    user_id=user_id,
                                    type=review_type,
                                    number=number,
                                    text=text)
        await callback.message.answer("Отзыв отправлен. Спасибо!")
        await state.clear()
    except Exception as e:
        print(f"Ошибка в send_done_review для user_id {user_id}: {e}")


@women_review_router.callback_query(F.data == "cancel_review")
async def cancel_last_review(callback_query: CallbackQuery, state: FSMContext):
    """
    Отмена отправки отзыва в базу данных
    """
    try:
        await state.clear()
        await callback_query.message.answer(text="Отзыв отменен")
    except Exception as e:
        print(f"Ошибка в cancel_last_review для "
              f"user_id {callback_query.from_user.id}: {e}")
