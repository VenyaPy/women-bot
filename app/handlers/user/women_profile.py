from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery

import re
from aiogram import types

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.exc import SQLAlchemyError

from app.database.models.users import SessionLocal
from app.database.requests.crud import get_user_info, get_user_city, create_profile
from app.templates.keyboards.inline_buttons import women_subscribe, enough_photo_women

women_profile_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


class WomenProfile(StatesGroup):
    name = State()
    age = State()
    weight = State()
    height = State()
    breast_size = State()
    hourly_rate = State()
    apartments = State()
    outcall = State()
    photos = State()
    phone_number = State()  # New state for phone number



@women_profile_router.message(F.text == "Добавить анкету")
async def add_women_profile(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        with SessionManager() as db:
            info = get_user_info(db=db, user_id=user_id)

        sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)

        if info.subscription_status.lower() != "true":
            await message.answer(text="Чтобы воспользоваться этой функцией необходимо оформить подписку:",
                                 reply_markup=sub_inline)
            return

        await state.set_state(WomenProfile.name)
        await message.answer("Введите ваше имя, например: Ирина")
    except Exception as e:
        await message.answer("Произошла ошибка при добавлении профиля. Попробуйте еще раз.")
        print(f"Error in add_profile: {e}")

@women_profile_router.message(WomenProfile.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваш возраст, например: 25")
    await state.set_state(WomenProfile.age)

@women_profile_router.message(WomenProfile.age)
async def process_age(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(age=int(message.text))
        await message.answer("Введите ваш вес в кг, например: 55")
        await state.set_state(WomenProfile.weight)
    else:
        await message.answer("Введите возраст цифрами, например: 25")

@women_profile_router.message(WomenProfile.weight)
async def process_weight(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(weight=int(message.text))
        await message.answer("Введите ваш рост в см, например: 165")
        await state.set_state(WomenProfile.height)
    else:
        await message.answer("Введите вес цифрами в кг, например: 55")

@women_profile_router.message(WomenProfile.height)
async def process_height(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(height=int(message.text))
        await message.answer("Введите размер груди, например: 90")
        await state.set_state(WomenProfile.breast_size)
    else:
        await message.answer("Введите рост цифрами в см, например: 170")

@women_profile_router.message(WomenProfile.breast_size)
async def process_breast_size(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(breast_size=message.text)
        await message.answer("Введите вашу цену за час в рублях, например: 2000")
        await state.set_state(WomenProfile.hourly_rate)
    else:
        await message.answer("Введите размер груди, например: 3")

@women_profile_router.message(WomenProfile.hourly_rate)
async def process_hourly_rate(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(hourly_rate=int(message.text))
        await message.answer("Введите ваш номер телефона в формате: 8 *** *** ** **")
        await state.set_state(WomenProfile.phone_number)
    else:
        await message.answer("Введите цену за час цифрами, например: 2000")


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


@women_profile_router.message(WomenProfile.phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    formatted_number = format_phone_number(message.text)
    if "Ошибка" in formatted_number:
        await message.answer(formatted_number)
    else:
        await state.update_data(phone_number=formatted_number)
        data = await state.get_data()
        await message.answer(f"Проверьте введенные данные:\nИмя: {data['name']}\nВозраст: {data['age']}\nВес: {data['weight']}\nРост: {data['height']}\nРазмер груди: {data['breast_size']}\nЦена за час: {data['hourly_rate']}\nТелефон: {formatted_number}\nПринимаете в апартаментах? Ответьте 'Да' или 'Нет'")
        await state.set_state(WomenProfile.apartments)

@women_profile_router.message(WomenProfile.apartments)
async def process_apartments(message: Message, state: FSMContext):
    if message.text.lower() in ['да', 'нет']:
        await state.update_data(apartments=message.text.lower())
        await message.answer("Работаете ли на выезд?\n\nОтветьте 'Да' или 'Нет'")
        await state.set_state(WomenProfile.outcall)
    else:
        await message.answer("Ответьте 'Да' или 'Нет'")

@women_profile_router.message(WomenProfile.outcall)
async def process_outcall(message: Message, state: FSMContext):
    if message.text.lower() in ['да', 'нет']:
        await state.update_data(outcall=message.text.lower())
        await message.answer("Пожалуйста, загрузите до 3 фотографий.")
        await state.set_state(WomenProfile.photos)
    else:
        await message.answer("Ответьте 'Да' или 'Нет'")

@women_profile_router.message(WomenProfile.photos)
async def process_photos(message: Message, state: FSMContext):
    user_data = await state.get_data()
    photos_list = user_data.get("photos", [])
    inline_done_photo = InlineKeyboardMarkup(inline_keyboard=enough_photo_women)

    photo_count = len(message.photo)
    try:
        for index, photo in enumerate(message.photo):
            photo_file_id = photo.file_id
            file_path = f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{message.from_user.id}_{len(photos_list)+1}.jpg"
            await message.bot.download(file=photo_file_id, destination=file_path)
            photos_list.append(file_path)

            if index == photo_count - 1:  # After processing all photos in the message
                profile_preview = f"Имя: {user_data['name']}\nВозраст: {user_data['age']}\nВес: {user_data['weight']}\nРост: {user_data['height']}\nРазмер груди: {user_data['breast_size']}\nЦена за час: {user_data['hourly_rate']}\nТелефон: {user_data['phone_number']}\nПринимает в апартаментах: {'Да' if user_data['apartments'] == 'да' else 'Нет'}\nНа выезд: {'Да' if user_data['outcall'] == 'да' else 'Нет'}"
                await message.answer(profile_preview)
                if len(photos_list) < 3:
                    await message.answer("Вы можете загрузить еще фото или сохранить анкету.", reply_markup=inline_done_photo)
                else:
                    await message.answer("Добавить вашу анкету?", reply_markup=inline_done_photo)

        await state.update_data(photos=photos_list)
    except Exception as e:
        await message.answer("Произошла ошибка при загрузке фотографий. Попробуйте еще раз.")
        print(f"Error processing photos: {e}")


@women_profile_router.callback_query(F.data == "enough_photos")
async def send_women_profile_to_bd(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback_query.from_user.id
    try:
        with SessionLocal() as db:
            city = get_user_city(db=db, user_id=user_id)
            create_profile(
                db=db,
                user_id=user_id,
                name=data.get("name", ""),
                age=int(data.get("age", 0)),
                weight=int(data.get("weight", 0)),
                height=int(data.get("height", 0)),
                breast_size=data.get("breast_size", ""),
                hourly_rate=int(data.get("hourly_rate", 0)),
                phone_number=data.get("phone_number", ""),
                apartments=data.get("apartments", "").lower() == "да",
                outcall=data.get("outcall", "").lower() == "да",
                photos=";".join(data.get("photos", [])),
                city=city
            )
            await callback_query.message.answer("Ваша анкета успешно создана")
            await callback_query.answer()
            await state.clear()
    except SQLAlchemyError as db_err:
        await callback_query.message.answer("Ошибка при сохранении профиля. Попробуйте еще раз.")
        print(f"Database error: {db_err}")
    except Exception as e:
        await callback_query.message.answer("Произошла непредвиденная ошибка при сохранении профиля.")
        print(f"General error: {e}")


@women_profile_router.callback_query(F.data == "cancel_send_profile")
async def cancel_send_profile(callback_query: CallbackQuery, state: FSMContext):
    if F.data == "cancel_send_profile":
        await state.clear()
        await callback_query.message.answer(text="Данные об анкете удалены!")
