import asyncio
from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re

from app.database.models.users import SessionLocal
from app.database.requests.crud import get_user_info, get_positive_reviews, get_negative_reviews
from app.templates.keyboards.inline_buttons import women_subscribe, add_or_not_add_review

women_check_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


@women_check_router.callback_query(F.data == "dont_want_to_add")
async def cancel_want_review(callback_query: CallbackQuery):
    await callback_query.message.delete()
    await callback_query.message.answer(text="Ваше желание учтено!")


class CheckPhoneNumber(StatesGroup):
    waiting_for_number = State()
    checking_review = State()


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


async def schedule_review_request(bot: Bot, chat_id: int, phone_number: str):
    await asyncio.sleep(10)  # Ожидаем 3 часа (10800 секунд)
    inline_add_review = InlineKeyboardMarkup(inline_keyboard=add_or_not_add_review)
    await bot.send_message(chat_id, text=f"Оставьте отзыв о номере {phone_number}. "
                                         f"Это поможет другим индивидуалкам избежать "
                                         f"неприятностей.", reply_markup=inline_add_review)


def get_reviews(db, phone_number):
    positive_reviews = get_positive_reviews(db, phone_number)
    negative_reviews = get_negative_reviews(db, phone_number)
    return positive_reviews, negative_reviews


def format_reviews(reviews, review_type):
    formatted_reviews = []
    for review in reviews:
        formatted_review = (f"\n<b>Тип отзыва:</b> {review_type}\n"
                            f"<b>Дата:</b> {review.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"<b>Отзыв:</b> {review.review_text}\n")
        formatted_reviews.append(formatted_review)
    return formatted_reviews


@women_check_router.message(F.text == "Проверить номер")
async def check_number(message: Message, state: FSMContext):
    user_id = message.from_user.id
    with SessionManager() as db:
        info = get_user_info(db=db, user_id=user_id)

    sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)

    if info.subscription_type not in ["Проверка", "Проверка + Анкета"]:
        await message.answer(text="Чтобы воспользоваться этой функцией необходимо оформить подписку (автоматически продлевается каждый месяц):",
                             reply_markup=sub_inline)
        return

    await state.set_state(CheckPhoneNumber.waiting_for_number)
    await message.answer(text="Введите номер телефона в формате: 8 *** *** ** **")



@women_check_router.message(CheckPhoneNumber.waiting_for_number)
async def process_phone_number(message: Message, state: FSMContext):
    try:
        phone_number = message.text
        formatted_number = format_phone_number(phone_number)

        if formatted_number.startswith("Ошибка"):
            await message.answer(text=formatted_number)
            await message.answer(text="Введите номер телефона в формате: 8 *** *** ** **")
        else:
            with SessionManager() as db:
                positive_reviews, negative_reviews = get_reviews(db, formatted_number)

            response = ""
            if positive_reviews or negative_reviews:
                response = "Вот что нашлось:\n"
                all_reviews = (format_reviews(positive_reviews, "Положительный") +
                               format_reviews(negative_reviews, "Негативный"))
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
        await message.answer("Произошла ошибка при обработке номера телефона.")
        print(f"Error in process_phone_number: {e}")



