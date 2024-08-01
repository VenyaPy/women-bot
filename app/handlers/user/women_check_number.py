import asyncio
import sys

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import (InlineKeyboardMarkup,
                           Message,
                           CallbackQuery,
                           InlineKeyboardButton)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re

from app.database.models.users import async_session_maker
from app.database.requests.crud import (get_user_info,
                                        get_positive_reviews,
                                        get_negative_reviews)
from app.templates.keyboards.inline_buttons import women_subscribe

women_check_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = async_session_maker()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()


@women_check_router.callback_query(F.data == "dont_want_to_add")
async def cancel_want_review(callback_query: CallbackQuery):
    """
    Отказ от оставления отзыва о номере телефона.
    """
    user_id = callback_query.from_user.id
    try:
        await callback_query.message.delete()
        await callback_query.message.answer(text="Ваше желание учтено!")
    except Exception as e:
        print(f"Error in cancel_want_review for user_id {user_id}: {e}")


class CheckPhoneNumber(StatesGroup):
    waiting_for_number = State()
    checking_review = State()
    adding_review = State()


def format_phone_number(phone_number: str) -> str:
    """Форматирование номера телефона в формат 8 *** *** ** **"""
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


async def schedule_review_request(bot: Bot, chat_id: int, phone_number: str):
    """
    После проверки номера телефона через 3 часа человеку приходит
    предложение оставить отзыв о номере телефона
    """
    try:
        await asyncio.sleep(10800)

        formatted_phone_number = phone_number.replace(" ", "")

        add_or_not_add_review = [
            [
                InlineKeyboardButton(text="Добавить отзыв",
                                     callback_data=f"want_to_add_review_{formatted_phone_number}")
            ],
            [
                InlineKeyboardButton(text="Не хочу добавлять",
                                     callback_data="dont_want_to_add")
            ]
        ]

        inline_add_review = InlineKeyboardMarkup(inline_keyboard=add_or_not_add_review)
        await bot.send_message(chat_id,
                               text=f"Оставьте отзыв о номере {phone_number}. "
                                    f"Это поможет другим девушкам избежать "
                                    f"неприятностей.",
                               reply_markup=inline_add_review)
    except Exception as e:
        print(f"Error in schedule_review_request for chat_id {chat_id}: {e}")


async def get_reviews(db, phone_number):
    """
    Получение отзывов о номере телефона
    """
    try:
        positive_reviews = await get_positive_reviews(db, phone_number)
        negative_reviews = await get_negative_reviews(db, phone_number)
        return positive_reviews, negative_reviews
    except Exception as e:
        print(f"Error in get_reviews for phone_number {phone_number}: {e}")
        return [], []


def format_reviews(reviews, review_type):
    """
    Форматирование отзывов в необходимый формат
    """
    try:
        formatted_reviews = []
        for review in reviews:
            formatted_review = (f"\n<b>Тип отзыва:</b> {review_type}\n"
                                f"<b>Дата:</b> {review.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                                f"<b>Отзыв:</b> {review.review_text}\n")
            formatted_reviews.append(formatted_review)
        return formatted_reviews
    except Exception as e:
        print(f"Error in format_reviews for review_type {review_type}: {e}")
        return []


@women_check_router.message(Command("finish"))
async def shutdown_bot(message: Message):
    await message.bot.session.close()
    sys.exit()


@women_check_router.message(F.text == "Проверить номер")
async def check_number(message: Message, state: FSMContext):
    """
    Если у женщины оформлена подписка, то она может проверить
    отзывы о номере телефона (мужчине)
    """
    user_id = message.from_user.id
    try:
        async with SessionManager() as db:
            info = await get_user_info(db=db, user_id=user_id)
    except Exception as e:
        print(f"Error in check_number while getting user info for user_id {user_id}: {e}")
        await message.answer("Произошла ошибка при проверке подписки.")
        return

    try:
        sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)

        if info.subscription_type not in ["Проверка", "Проверка + Анкета"]:
            await message.answer(text="Чтобы воспользоваться этой функцией необходимо "
                                      "оформить подписку (автоматически "
                                      "продлевается каждый месяц):",
                                 reply_markup=sub_inline)
            return

        await state.set_state(CheckPhoneNumber.waiting_for_number)
        await message.answer(text="Введите номер телефона в формате: 8 *** *** ** **")
    except Exception as e:
        print(f"Error in check_number for user_id {user_id}: {e}")


@women_check_router.message(CheckPhoneNumber.waiting_for_number)
async def process_phone_number(message: Message, state: FSMContext):
    """
    Ожидание ввода номера телефона и последующее его форматирование
    """
    user_id = message.from_user.id
    try:
        phone_number = message.text
        formatted_number = format_phone_number(phone_number)

        if formatted_number.startswith("Ошибка"):
            await message.answer(text=formatted_number)
            await message.answer(text="Введите номер телефона в формате: 8 *** *** ** **")
        else:
            try:
                async with SessionManager() as db:
                    positive_reviews, negative_reviews = await get_reviews(db,
                                                                           formatted_number)
            except Exception as e:
                print(f"Error in process_phone_number while getting reviews "
                      f"for user_id {user_id}: {e}")
                await message.answer("Произошла ошибка при получении отзывов.")
                return

            try:
                response = ""
                if positive_reviews or negative_reviews:
                    response = "Вот что нашлось:\n"
                    all_reviews = (format_reviews(positive_reviews,
                                                  "Положительный") +
                                   format_reviews(negative_reviews,
                                                  "Негативный"))
                    for review in all_reviews:
                        if len(response) + len(review) > 4096:
                            await message.answer(text=response)
                            response = review
                        else:
                            response += review
                else:
                    response = "Негативных отзывов не найдено. Рейтинг положительный."

                await message.answer(text=response)

                await state.update_data(phone_number=formatted_number)
                await state.set_state(CheckPhoneNumber.checking_review)

                await asyncio.create_task(schedule_review_request(message.bot,
                                                                  message.chat.id,
                                                                  formatted_number))
            except Exception as e:
                print(f"Error in process_phone_number while formatting or "
                      f"sending reviews for user_id {user_id}: {e}")
                await message.answer("Произошла ошибка при обработке отзывов.")
    except Exception as e:
        print(f"Error in process_phone_number for user_id {user_id}: {e}")
