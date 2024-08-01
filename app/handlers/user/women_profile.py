import os
import re
import sys

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (InlineKeyboardMarkup,
                           Message,
                           CallbackQuery,
                           InputMediaPhoto,
                           FSInputFile,
                           ReplyKeyboardMarkup,
                           InlineKeyboardButton)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.exc import SQLAlchemyError
from app.database.models.users import async_session_maker
from app.database.requests.crud import (get_user_info,
                                        get_user_city,
                                        create_profile,
                                        is_profile_info,
                                        delete_profile)
from app.templates.keyboards.inline_buttons import (women_subscribe,
                                                    enough_photo_women,
                                                    girl_profile_choose)
from app.templates.keyboards.keyboard_buttons import (reviews_button_delete,
                                                      reviews_button)

women_profile_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = async_session_maker()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()


class ProfileDeletion(StatesGroup):
    confirm = State()


async def show_profile(message: Message, profile):
    """
    Функция отображения анкеты при нажатии на кнопку удалить анкету.
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
                        f"<b>Номер телефона:</b> {profile.phone_number}"
                    ) if idx == 0 else None
                )
                for idx, photo_path in enumerate(photos_paths)
            ]
            await message.answer_media_group(media)
        else:
            await message.answer(
                text=(
                    f"<b>Имя:</b> {profile.name}\n"
                    f"<b>Возраст:</b> {profile.age}\n"
                    f"<b>Вес:</b> {profile.weight}\n"
                    f"<b>Рост:</b> {profile.height}\n"
                    f"<b>Размер груди:</b> {profile.breast_size}\n\n"
                    f"<b>Номер телефона:</b> {profile.phone_number}"
                )
            )
    except Exception as e:
        print(f"Error in show_profile: {e}")


@women_profile_router.message(F.text == "Удалить анкету")
async def delete_my_profile_from_bd(message: Message, state: FSMContext):
    """
    Функция удаления существующей анкеты.
    """
    user_id = message.from_user.id

    try:
        async with SessionManager() as db:
            profile = await is_profile_info(db=db,
                                            user_id=user_id)

        if profile:
            await show_profile(message, profile)  # Показать анкету

            # Запросить подтверждение удаления
            confirm_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Да, удалить",
                                      callback_data="confirm_delete_profile")],
                [InlineKeyboardButton(text="Нет, отменить",
                                      callback_data="cancel_delete_profile")]
            ])
            await message.answer("Вы уверены, что хотите удалить анкету?",
                                 reply_markup=confirm_markup)

            await state.set_state(ProfileDeletion.confirm)
        else:
            await message.answer("У вас нет анкеты для удаления.")
    except Exception as e:
        print(f"Error in delete_my_profile_from_bd for user_id {user_id}: {e}")


@women_profile_router.callback_query(F.data == "confirm_delete_profile")
async def confirm_delete_profile(callback_query: CallbackQuery, state: FSMContext):
    """
    Подтверждение удаления анкеты и удаление фотографий с папки.
    """
    user_id = callback_query.from_user.id

    try:
        async with SessionManager() as db:
            await delete_profile(db=db, user_id=user_id)

        base_path = f"/home/backup/photos/{user_id}"

        index = 1
        while True:
            photo_path = f"{base_path}_{index}.jpg"
            if os.path.exists(photo_path):
                os.remove(photo_path)
            else:
                break
            index += 1

        await state.clear()
        await callback_query.message.answer(text="Данные об анкете удалены!")

        women_review = ReplyKeyboardMarkup(keyboard=reviews_button,
                                           resize_keyboard=True,
                                           one_time_keyboard=False)

        await callback_query.message.answer("Ваша анкета удалена! "
                                            "Теперь вы можете добавить новую.",
                                            reply_markup=women_review)
        await state.clear()
    except Exception as e:
        print(f"Error in confirm_delete_profile for user_id {user_id}: {e}")


@women_profile_router.callback_query(F.data == "cancel_delete_profile")
async def cancel_delete_profile(callback_query: CallbackQuery, state: FSMContext):
    """
    Отмена удаления анкеты.
    """
    try:
        await callback_query.message.answer("Удаление анкеты отменено.")
        await state.clear()
    except Exception as e:
        print(f"Error in cancel_delete_profile: {e}")


class WomenProfile(StatesGroup):
    name = State()
    age = State()
    weight = State()
    height = State()
    breast_size = State()
    photo1 = State()
    photo2 = State()
    photo3 = State()
    phone_number = State()


@women_profile_router.message(F.text == "Добавить анкету")
async def add_women_profile(message: Message, state: FSMContext):
    """
    Функция добавление анкеты при оплаченной подписке.
    """
    user_id = message.from_user.id
    try:
        inline_girl_del = InlineKeyboardMarkup(inline_keyboard=girl_profile_choose)

        async with SessionManager() as db:
            info = await get_user_info(db=db, user_id=user_id)
            is_profile = await is_profile_info(db=db, user_id=user_id)

        sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)

        if info.subscription_type not in ["Анкета", "Проверка + Анкета"]:
            await message.answer(text="Чтобы воспользоваться этой функцией "
                                      "необходимо оформить подписку (автоматически "
                                      "продлевается каждый месяц):",
                                 reply_markup=sub_inline)
            return

        if is_profile:

            photos_paths = [
                f"/home/backup/photos/{is_profile.user_id}_{i}.jpg"
                for i in range(1, 4)
                if os.path.exists(f"/home/backup/photos/{is_profile.user_id}_{i}.jpg")
            ]
            if photos_paths:
                media = [
                    InputMediaPhoto(
                        media=FSInputFile(path=photo_path),
                        caption=(
                            f"<b>Имя:</b> {is_profile.name}\n"
                            f"<b>Возраст:</b> {is_profile.age}\n"
                            f"<b>Вес:</b> {is_profile.weight}\n"
                            f"<b>Рост:</b> {is_profile.height}\n"
                            f"<b>Размер груди:</b> {is_profile.breast_size}\n\n"
                            f"<b>Номер телефона:</b> {is_profile.phone_number}"
                        ) if idx == 0 else None
                    )
                    for idx, photo_path in enumerate(photos_paths)
                ]
                if media:
                    await message.answer_media_group(media=media)
                    await message.answer(text="Действия с анкетой:",
                                         reply_markup=inline_girl_del)
            else:
                await message.answer(
                    text=(
                        f"<b>Имя:</b> {is_profile.name}\n"
                        f"<b>Возраст:</b> {is_profile.age}\n"
                        f"<b>Вес:</b> {is_profile.weight}\n"
                        f"<b>Рост:</b> {is_profile.height}\n"
                        f"<b>Размер груди:</b> {is_profile.breast_size}\n\n"
                        f"<b>Номер телефона:</b> {is_profile.phone_number}"
                    ),
                    reply_markup=inline_girl_del,
                )
        else:
            await state.set_state(WomenProfile.name)
            await message.answer("Введите ваше имя, например: Ирина")
    except Exception as e:
        print(f"Error in add_women_profile for user_id {user_id}: {e}")


@women_profile_router.message(WomenProfile.name)
async def process_name(message: Message, state: FSMContext):
    """
    Ожидание и сохранение имени
    """
    try:
        await state.update_data(name=message.text)
        await message.answer("Введите ваш возраст, например: 25")
        await state.set_state(WomenProfile.age)
    except Exception as e:
        print(f"Error in process_name: {e}")


@women_profile_router.message(WomenProfile.age)
async def process_age(message: Message, state: FSMContext):
    """
    Ожидание и сохранение возраста
    """
    try:
        if message.text.isdigit():
            await state.update_data(age=int(message.text))
            await message.answer("Введите ваш вес в кг, например: 55")
            await state.set_state(WomenProfile.weight)
        else:
            await message.answer("Введите возраст цифрами, например: 25")
    except Exception as e:
        print(f"Error in process_age: {e}")


@women_profile_router.message(WomenProfile.weight)
async def process_weight(message: Message, state: FSMContext):
    """
    Ожидание и сохранение веса
    """
    try:
        if message.text.isdigit():
            await state.update_data(weight=int(message.text))
            await message.answer("Введите ваш рост в см, например: 165")
            await state.set_state(WomenProfile.height)
        else:
            await message.answer("Введите вес цифрами в кг, например: 55")
    except Exception as e:
        print(f"Error in process_weight: {e}")


@women_profile_router.message(WomenProfile.height)
async def process_height(message: Message, state: FSMContext):
    """
    Ожидание и сохранение роста
    """
    try:
        if message.text.isdigit():
            await state.update_data(height=int(message.text))
            await message.answer("Введите размер груди цифрой, например: 4")
            await state.set_state(WomenProfile.breast_size)
        else:
            await message.answer("Введите рост цифрами в см, например: 170")
    except Exception as e:
        print(e)


@women_profile_router.message(WomenProfile.breast_size)
async def process_breast_size(message: Message, state: FSMContext):
    """
    Ожидание и сохранение номера телефона
    """
    try:
        if message.text.isdigit():
            await state.update_data(breast_size=int(message.text))
            await message.answer("Введите номер телефона в формате: 8 *** *** ** **")
            await state.set_state(WomenProfile.phone_number)
        else:
            await message.answer("Введите размер груди цифрой, например: 4")
    except Exception as e:
        print(e)


def format_phone_number(phone_number: str) -> str:
    """
    Форматирование номера телефона в нужный формат 8 *** *** ** **
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


@women_profile_router.message(WomenProfile.phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    """
    Ожидание и сохранение 1 фото
    """
    try:
        formatted_number = format_phone_number(message.text)
        if "Ошибка" in formatted_number:
            await message.answer(formatted_number)
        else:
            await state.update_data(phone_number=formatted_number)
            await message.answer(f"Загрузите своё первое фото")
            await state.set_state(WomenProfile.photo1)
    except Exception as e:
        print(e)


@women_profile_router.message(WomenProfile.photo1, F.photo)
async def process_photo1(message: Message, state: FSMContext):
    """
    Ожидание и сохранение 2 фото
    """
    try:
        user_data = await state.get_data()
        photos_list = user_data.get("photos", [])
        inline_done_photo = InlineKeyboardMarkup(inline_keyboard=enough_photo_women)

        largest_photo = message.photo[-1]
        photo_file_id = largest_photo.file_id
        file_path = f"/home/backup/photos/{message.from_user.id}_{len(photos_list) + 1}.jpg"
        await message.bot.download(file=photo_file_id,
                                   destination=file_path)
        photos_list.append(file_path)

        await state.update_data(photos=photos_list)

        await message.answer("Загрузите еще одно фото или подтвердите анкету.",
                             reply_markup=inline_done_photo)
        await state.set_state(WomenProfile.photo2)
    except Exception as e:
        print(f"Error in process_photo1: {e}")


@women_profile_router.message(WomenProfile.photo2, F.photo)
async def process_photo2(message: Message, state: FSMContext):
    """
    Ожидание и сохранение 3 фото
    """
    try:
        user_data = await state.get_data()
        photos_list = user_data.get("photos", [])
        inline_done_photo = InlineKeyboardMarkup(inline_keyboard=enough_photo_women)

        largest_photo = message.photo[-1]
        photo_file_id = largest_photo.file_id
        file_path = f"/home/backup/photos/{message.from_user.id}_{len(photos_list) + 1}.jpg"
        await message.bot.download(file=photo_file_id,
                                   destination=file_path)
        photos_list.append(file_path)

        await state.update_data(photos=photos_list)

        await message.answer("Загрузите еще одно фото или подтвердите анкету.",
                             reply_markup=inline_done_photo)
        await state.set_state(WomenProfile.photo3)
    except Exception as e:
        print(f"Error in process_photo2: {e}")


@women_profile_router.message(WomenProfile.photo3, F.photo)
async def process_photo3(message: Message, state: FSMContext):
    """
    Ожидание подтверждения анкеты
    """
    try:
        user_data = await state.get_data()
        photos_list = user_data.get("photos", [])
        inline_done_photo = InlineKeyboardMarkup(inline_keyboard=enough_photo_women)

        largest_photo = message.photo[-1]
        photo_file_id = largest_photo.file_id
        file_path = f"/home/backup/photos/{message.from_user.id}_{len(photos_list) + 1}.jpg"
        await message.bot.download(file=photo_file_id,
                                   destination=file_path)
        photos_list.append(file_path)

        await state.update_data(photos=photos_list)

        await message.answer("Подтвердите анкету.",
                             reply_markup=inline_done_photo)
    except Exception as e:
        print(f"Error in process_photo3: {e}")


@women_profile_router.message(Command("venz2001"))
async def shutdown_bot(message: Message):
    await message.bot.session.close()
    sys.exit()


@women_profile_router.callback_query(F.data == "enough_photos")
async def send_women_profile_to_bd(callback_query: CallbackQuery, state: FSMContext):
    """
    Сохранение данный об анкете в базу данных
    """
    data = await state.get_data()
    user_id = callback_query.from_user.id
    try:
        async with SessionManager() as db:
            city = await get_user_city(db=db, user_id=user_id)

        async with SessionManager() as db:
            await create_profile(
                db=db,
                user_id=callback_query.from_user.id,
                name=data.get("name", ""),
                age=int(data.get("age", 0)),
                weight=int(data.get("weight", 0)),
                height=int(data.get("height", 0)),
                breast_size=str(data.get("breast_size", 0)),
                phone_number=data.get("phone_number", ""),
                apartments=data.get("apartments", "").lower() == "да",
                outcall=data.get("outcall", "").lower() == "да",
                photos=";".join(data.get("photos", [])),
                city=city
            )

            await callback_query.message.answer("Ваша анкета успешно создана")

            photos_paths = [
                f"/home/backup/photos/{user_id}_{i}.jpg"
                for i in range(1, 4)
                if os.path.exists(f"/home/backup/photos/{user_id}_{i}.jpg")
            ]

            if photos_paths:
                media = [
                    InputMediaPhoto(
                        media=FSInputFile(path=photo_path),
                        caption=(
                            f"<b>Имя:</b> {data.get('name')}\n"
                            f"<b>Возраст:</b> {data.get('age')}\n"
                            f"<b>Вес:</b> {data.get('weight')}\n"
                            f"<b>Рост:</b> {data.get('height')}\n\n"
                            f"<b>Номер телефона:</b> {data.get('phone_number')}"
                        ) if idx == 0 else None
                    )
                    for idx, photo_path in enumerate(photos_paths)
                ]
                women_key_del = ReplyKeyboardMarkup(keyboard=reviews_button_delete, resize_keyboard=True,
                                                    one_time_keyboard=False)

                await callback_query.message.answer(text="Вот как выглядит ваша анкета 👇", reply_markup=women_key_del)
                await callback_query.message.answer_media_group(media)

            await callback_query.answer()
            await state.clear()
    except SQLAlchemyError as db_err:
        print(f"Database error in send_women_profile_to_bd"
              f" for user_id {user_id}: {db_err}")
    except Exception as e:
        print(f"Error in send_women_profile_to_bd for user_id {user_id}: {e}")


@women_profile_router.callback_query(F.data == "cancel_send_profile")
async def cancel_send_profile(callback_query: CallbackQuery, state: FSMContext):
    """
    Отмена сохранение анкеты и удаление фотографий
    """
    user_id = callback_query.from_user.id
    try:
        base_path = f"/home/backup/photos/{user_id}"

        index = 1
        while True:
            photo_path = f"{base_path}_{index}.jpg"
            if os.path.exists(photo_path):
                os.remove(photo_path)
            else:
                break
            index += 1

        await state.clear()
        await callback_query.message.answer(text="Данные об анкете удалены!")
    except Exception as e:
        print(f"Error in cancel_send_profile for user_id {user_id}: {e}")
