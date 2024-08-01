import os
from aiogram import Router, F
from aiogram.types import (CallbackQuery,
                           InlineKeyboardMarkup,
                           Message,
                           InputMediaPhoto,
                           FSInputFile,
                           ReplyKeyboardMarkup,
                           KeyboardButton)
from app.database.models.users import async_session_maker
from app.database.requests.crud import (get_user_city,
                                        get_all_profiles)
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
    """
    Функция определения конкретной анкеты, на которой находится юзер.
    Если пользователь ещё не имеет такой анкеты, то устанавливается 0 значение.
    """
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
    """
    Функция кнопок на клавиатуре, которая
    позволяет перемещаться по анкетам женщин вправо.
    """
    try:
        user_id = message.from_user.id
        async with SessionManager() as db:
            city = await get_user_city(db=db, user_id=user_id)
            profiles = await get_all_profiles(db, city=city)

        if user_id not in current_profile_index:
            current_profile_index[user_id] = 0

        current_profile_index[user_id] = (current_profile_index[user_id] + 1) % len(profiles)
        prev_next_button = await get_prev_next_button(user_id, len(profiles))
        await send_profile(message, profiles[current_profile_index[user_id]], prev_next_button)
    except Exception as e:
        print(f"Ошибка при нажатии на >>>: {e}")


@men_router.message(F.text.regexp(r'^<<<'))
async def prev_profile(message: Message):
    """
    Функция кнопок на клавиатуре, которая
    позволяет перемещаться по анкетам женщин влево.
    """
    try:
        user_id = message.from_user.id
        async with SessionManager() as db:
            city = await get_user_city(db=db, user_id=user_id)
            profiles = await get_all_profiles(db, city=city)

        if user_id not in current_profile_index:
            current_profile_index[user_id] = 0

        current_profile_index[user_id] = (current_profile_index[user_id] - 1) % len(profiles)
        prev_next_button = await get_prev_next_button(user_id,
                                                      len(profiles))
        await send_profile(message,
                           profiles[current_profile_index[user_id]],
                           prev_next_button)
    except Exception as e:
        print(f"Ошибка при нажатии на кнопку <<<: {e}")


async def send_profile(message: Message, profile, prev_next_button):
    """
    Функция, которая отправляет определенную анкету, заданную кнопками >>> или <<<.
    """
    try:
        photos_paths = [
            f"/home/backup/photos/{profile.user_id}_{i}.jpg"
            for i in range(1, 4)
            if os.path.exists(f"/home/backup/photos/{profile.user_id}_{i}.jpg")
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
                        f"<b>Размер груди:</b> {profile.breast_size}\n\n"
                        f"<b>Номер телефона:</b> {profile.phone_number}"
                    ) if idx == 0 else None
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
                     f"<b>Размер груди:</b> {profile.breast_size}\n\n"
                     f"\n\n<b>Номер телефона:</b> {profile.phone_number}",
                reply_markup=ReplyKeyboardMarkup(keyboard=prev_next_button,
                                                 resize_keyboard=True,
                                                 one_time_keyboard=False)
            )
    except Exception as e:
        print(f"Ошибка при отправке профиля в men_menu: {e}")


@men_router.callback_query(F.data == "other_city_callback")
async def change_city(callback_query: CallbackQuery):
    """
    Функция обновления города мужчины.
    Функция доступна при отсутствии доступных анкет в городе.
    """
    try:
        await callback_query.message.delete()
        city_inline = InlineKeyboardMarkup(inline_keyboard=city_choose)
        await callback_query.message.answer(text="Выберите свой город:",
                                            reply_markup=city_inline)
    except Exception as e:
        print(f"Ошибка при смене города на другой: {e}")


@men_router.callback_query(F.data == "update_profile_list")
async def update_profile_for_mens(message: Message):
    """
    Также доступна при отсутствии анкет в городе.
    Возможно обновить список анкет.
    """
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
