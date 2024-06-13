import os

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, InputMediaPhoto, FSInputFile, ReplyKeyboardMarkup

from app.database.models.users import async_session_maker
from app.database.requests.crud import get_user_city, get_all_profiles
from app.templates.keyboards.inline_buttons import women_subscribe, city_choose, other_city
from app.templates.keyboards.keyboard_buttons import prev_next_button

men_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = async_session_maker()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()


current_profile_index = {}


@men_router.message(F.text.lower() == '>>>')
async def next_profile(message: Message):
    user_id = message.from_user.id
    async with SessionManager() as db:
        city = await get_user_city(db=db, user_id=user_id)
        profiles = await get_all_profiles(db, city=city)

    if user_id not in current_profile_index:
        current_profile_index[user_id] = 0

    current_profile_index[user_id] = (current_profile_index[user_id] + 1) % len(profiles)
    await send_profile(message, profiles[current_profile_index[user_id]])


@men_router.message(F.text.lower() == '<<<')
async def prev_profile(message: Message):
    user_id = message.from_user.id
    async with SessionManager() as db:
        city = await get_user_city(db=db, user_id=user_id)
        profiles = await get_all_profiles(db, city=city)

    if user_id not in current_profile_index:
        current_profile_index[user_id] = 0

    current_profile_index[user_id] = (current_profile_index[user_id] - 1) % len(profiles)
    await send_profile(message, profiles[current_profile_index[user_id]])


async def send_profile(message: Message, profile):
    service_info = []
    if profile.apartments:
        service_info.append("Принимаю в апартаментах")
    if profile.outcall:
        service_info.append("Работаю на выезд")
    service_text = " и ".join(service_info).capitalize()

    photos_paths = [f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{profile.user_id}_{i}.jpg" for i in range(1, 4) if
                    os.path.exists(f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{profile.user_id}_{i}.jpg")]
    if photos_paths:
        media = [InputMediaPhoto(media=FSInputFile(path=photo_path),
                                       caption=f"<b>Имя:</b> {profile.name}\n<b>Возраст:</b> {profile.age}\n"
                                               f"<b>Вес:</b> {profile.weight}\n<b>Рост:</b> {profile.height}\n"
                                               f"<b>Размер груди:</b> {profile.breast_size}\n"
                                               f"<b>Стоимость за час:</b> {profile.hourly_rate} руб\n\n"
                                               f"{service_text if service_text else 'Услуги не указаны'}\n\n"
                                               f"<b>Номер телефона:</b> <tg-spoiler>{profile.phone_number}</tg-spoiler>")
                 for photo_path in photos_paths]
        await message.answer_media_group(media)
    else:
        await message.answer(
            text=f"<b>Имя:</b> {profile.name}\n"
                 f"<b>Возраст:</b> {profile.age}\n"
                 f"<b>Вес:</b> {profile.weight}\n"
                 f"<b>Рост:</b> {profile.height}\n"
                 f"<b>Размер груди:</b> {profile.breast_size}\n"
                 f"<b>Стоимость за час:</b> {profile.hourly_rate} руб"
                 f"\n\n{service_text if service_text else 'Услуги не указаны'}"
                 f"\n\n<b>Номер телефона:</b> <tg-spoiler>{profile.phone_number}</tg-spoiler>",
            reply_markup=ReplyKeyboardMarkup(keyboard=prev_next_button, resize_keyboard=True, one_time_keyboard=False)
        )


@men_router.callback_query(F.data == "other_city_callback")
async def change_city(callback_query: CallbackQuery):
    await callback_query.message.delete()
    city_inline = InlineKeyboardMarkup(inline_keyboard=city_choose)
    await callback_query.message.answer(text="Выберите свой город:", reply_markup=city_inline)


@men_router.callback_query(F.data == "update_profile_list")
async def update_profile_for_mens(message: Message):
    user_id = message.from_user.id
    async with SessionManager() as db:
        city = await get_user_city(db=db, user_id=user_id)
        profiles = await get_all_profiles(db, city=city)

    if profiles:

        if user_id not in current_profile_index:
            current_profile_index[user_id] = 0

        current_profile_index[user_id] = (current_profile_index[user_id] + 1) % len(profiles)
        await send_profile(message, profiles[current_profile_index[user_id]])

    if not profiles:
        await message.answer(text="Анкет в вашем городе ещё нет")