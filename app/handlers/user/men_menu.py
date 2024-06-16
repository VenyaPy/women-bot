import os
from aiogram import Router, F, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, InputMediaPhoto, FSInputFile, \
    ReplyKeyboardMarkup, KeyboardButton
from app.database.models.users import async_session_maker
from app.database.requests.crud import get_user_city, get_all_profiles
from app.templates.keyboards.inline_buttons import city_choose

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


async def get_prev_next_button(user_id, total_profiles):
    try:
        if user_id not in current_profile_index:
            current_profile_index[user_id] = 0

        current_index = current_profile_index[user_id]

        buttons = [
            KeyboardButton(text=f"<<< ({(current_index - 1) % total_profiles + 1})"),
            KeyboardButton(text=f">>> ({(current_index + 1) % total_profiles + 1})")
        ]

        prev_next_button = [
            buttons,
            [
                KeyboardButton(text="Помощь")
            ]
        ]
        return prev_next_button
    except Exception as e:
        print(f"Ошибка при функции get_prev_next_button: {e}")


@men_router.message(F.text.regexp(r'^>>>'))
async def next_profile(message: Message):
    try:
        user_id = message.from_user.id
        async with SessionManager() as db:
            city = await get_user_city(db=db, user_id=user_id)
            profiles = await get_all_profiles(db, city=city)

        if user_id not in current_profile_index:
            current_profile_index[user_id] = 0

        # Обновляем индекс профиля, чтобы он возвращался к началу при достижении конца
        current_profile_index[user_id] = (current_profile_index[user_id] + 1) % len(profiles)
        prev_next_button = await get_prev_next_button(user_id, len(profiles))
        await send_profile(message, profiles[current_profile_index[user_id]], prev_next_button)
    except Exception as e:
        print(f"Ошибка при нажатии на >>>: {e}")


@men_router.message(F.text.regexp(r'^<<<'))
async def prev_profile(message: Message):
    try:
        user_id = message.from_user.id
        async with SessionManager() as db:
            city = await get_user_city(db=db, user_id=user_id)
            profiles = await get_all_profiles(db, city=city)

        if user_id not in current_profile_index:
            current_profile_index[user_id] = 0

        # Обновляем индекс профиля, чтобы он возвращался к концу при достижении начала
        current_profile_index[user_id] = (current_profile_index[user_id] - 1) % len(profiles)
        prev_next_button = await get_prev_next_button(user_id, len(profiles))
        await send_profile(message, profiles[current_profile_index[user_id]], prev_next_button)
    except Exception as e:
        print(f"Ошибка при нажатии на кнопку <<<: {e}")


async def send_profile(message: Message, profile, prev_next_button):
    try:
        service_info = []
        if profile.apartments:
            service_info.append("Принимаю в апартаментах")
        if profile.outcall:
            service_info.append("Работаю на выезд")
        service_text = " и ".join(service_info).capitalize()

        photos_paths = [
            f"/Users/venya/women-bot/app/database/photos/{profile.user_id}_{i}.jpg"
            for i in range(1, 4)
            if os.path.exists(f"/Users/venya/women-bot/app/database/photos/{profile.user_id}_{i}.jpg")
        ]
        if photos_paths:
            media = [
                InputMediaPhoto(
                    media=FSInputFile(path=photo_path),
                    caption=(
                        f"<b>Имя:</b> {profile.name}\n"
                        f"<b>Возраст:</b> {profile.age}\n"
                        f"<b>Вес:</b> {profile.weight}\n"
                        f"<b>Рост:</b> {profile.height}\n"
                        f"<b>Размер груди:</b> {profile.breast_size}\n"
                        f"<b>Стоимость за час:</b> {profile.hourly_rate} руб\n\n"
                        f"{service_text if service_text else 'Услуги не указаны'}\n\n"
                        f"<b>Номер телефона:</b> <tg-spoiler>{profile.phone_number}</tg-spoiler>"
                    ) if idx == 0 else None  # Подпись только для первой фотографии
                )
                for idx, photo_path in enumerate(photos_paths)
            ]
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
    except Exception as e:
        print(f"Ошибка при отправке профиля в men_menu: {e}")


@men_router.callback_query(F.data == "other_city_callback")
async def change_city(callback_query: CallbackQuery):
    try:
        await callback_query.message.delete()
        city_inline = InlineKeyboardMarkup(inline_keyboard=city_choose)
        await callback_query.message.answer(text="Выберите свой город:", reply_markup=city_inline)
    except Exception as e:
        print(f"Ошибка при смене города на другой: {e}")


@men_router.callback_query(F.data == "update_profile_list")
async def update_profile_for_mens(message: Message):
    try:
        user_id = message.from_user.id

        async with SessionManager() as db:
            city = await get_user_city(db=db, user_id=user_id)

        async with SessionManager() as db:
            profiles = await get_all_profiles(db, city=city)

        if profiles:
            if user_id not in current_profile_index:
                current_profile_index[user_id] = 0

            current_profile_index[user_id] = (current_profile_index[user_id] + 1) % len(profiles)
            prev_next_button = await get_prev_next_button(user_id, len(profiles))
            await send_profile(message, profiles[current_profile_index[user_id]], prev_next_button)
        else:
            await message.answer(text="Анкет в вашем городе ещё нет")
    except Exception as e:
        print(f"Ошибка при нажатии на кнопку обновить профили: {e}")