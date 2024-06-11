import os
import random
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, InputMediaPhoto, FSInputFile
from app.database.models.users import SessionLocal, User
from app.database.requests.crud import add_or_update_user, update_user_city, get_all_profiles, get_user_info, get_user_city
from app.handlers.admin.admin_start import admin_start_menu
from app.templates.keyboards.keyboard_buttons import prev_next_button, reviews_button
from app.templates.keyboards.inline_buttons import gender_start, city_choose, women_subscribe, politic_buttons, other_city
from app.templates.texts.user import message_command_start
from config import ADMINS

start_router = Router()

class SessionManager:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

@start_router.message(CommandStart())
async def start(message: Message):
    inline_politics = InlineKeyboardMarkup(inline_keyboard=politic_buttons)

    user_id = message.from_user.id

    if user_id in ADMINS:
        await admin_start_menu(message)
    else:
        with SessionManager() as db:
            is_user = get_user_info(db=db, user_id=message.from_user.id)
            city = get_user_city(db=db, user_id=user_id)

        if is_user and is_user.gender == "Мужчина":
            keyboard = ReplyKeyboardMarkup(keyboard=prev_next_button, resize_keyboard=True, one_time_keyboard=False)

            with SessionManager() as db:
                profiles = get_all_profiles(db=db, city=city)

            if not profiles:
                inline_other_city = InlineKeyboardMarkup(inline_keyboard=other_city)
                await message.answer("Анкет в вашем городе ещё нет", reply_markup=inline_other_city)
                return

            random_profile = random.choice(profiles)

            service_info = []
            if random_profile.apartments:
                service_info.append("Принимаю в апартаментах")
            if random_profile.outcall:
                service_info.append("Работаю на выезд")
            service_text = " и ".join(service_info).capitalize()

            photos_paths = [f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{random_profile.user_id}_{i}.jpg" for i in range(1, 4) if os.path.exists(f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{random_profile.user_id}_{i}.jpg")]
            if photos_paths:
                media = [InputMediaPhoto(media=FSInputFile(path=photo_path),
                                         caption=f"<b>Имя:</b> {random_profile.name}\n<b>Возраст:</b> {random_profile.age}\n"
                                                 f"<b>Вес:</b> {random_profile.weight}\n<b>Рост:</b> {random_profile.height}\n"
                                                 f"<b>Размер груди:</b> {random_profile.breast_size}\n"
                                                 f"<b>Стоимость за час:</b> {random_profile.hourly_rate} руб\n\n"
                                                 f"{service_text if service_text else 'Услуги не указаны'}\n\n"
                                                 f"<b>Номер телефона:</b> <tg-spoiler>{random_profile.phone_number}</tg-spoiler>")
                         for photo_path in photos_paths]
                await message.answer_media_group(media)
            else:
                await message.answer(
                    text=f"<b>Имя:</b> {random_profile.name}\n"
                         f"<b>Возраст:</b> {random_profile.age}\n"
                         f"<b>Вес:</b> {random_profile.weight}\n"
                         f"<b>Рост:</b> {random_profile.height}\n"
                         f"<b>Размер груди:</б> {random_profile.breast_size}\n"
                         f"<b>Стоимость за час:</б> {random_profile.hourly_rate} руб"
                         f"\n\n{service_text if service_text else 'Услуги не указаны'}"
                         f"\n\n<b>Номер телефона:</б> <tg-spoiler>{random_profile.phone_number}</tg-spoiler>",
                    reply_markup=keyboard
                )

        if is_user and is_user.gender == "Женщина":
            women_review = ReplyKeyboardMarkup(keyboard=reviews_button, resize_keyboard=True, one_time_keyboard=False)

            await message.answer(text=message_command_start, reply_markup=women_review)

        if not is_user:
            await message.answer(text=message_command_start, reply_markup=inline_politics)

            inline_gender = InlineKeyboardMarkup(inline_keyboard=gender_start)
            await message.answer(text="Выберите ваш пол:", reply_markup=inline_gender)


@start_router.callback_query(F.data.in_({"man_gender", "woman_gender"}))
async def process_gender_selection(callback_query: CallbackQuery):
    await callback_query.message.delete()
    user_id = callback_query.from_user.id

    gender = 'Мужчина' if callback_query.data == 'man_gender' else 'Женщина'

    with SessionManager() as db:
        add_or_update_user(user_id=user_id, gender=gender, db=db)

    city_inline = InlineKeyboardMarkup(inline_keyboard=city_choose)
    await callback_query.message.answer(text="Выберите свой город:", reply_markup=city_inline)


@start_router.callback_query(F.data.startswith('city_'))
async def process_city_selection(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    city_data = callback_query.data
    city = city_data.split('_', 1)[1]

    with SessionManager() as db:
        update_user_city(db=db, user_id=user_id, city=city)
        user = db.query(User).filter(User.user_id == user_id).first()
        gender = user.gender if user else None

    if gender == 'Женщина':
        await callback_query.message.delete()
        women_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)
        name = callback_query.from_user.first_name
        women_review = ReplyKeyboardMarkup(keyboard=reviews_button, resize_keyboard=True, one_time_keyboard=False)

        await callback_query.message.answer(text=f"Привет, {name}", reply_markup=women_review)
        await callback_query.message.answer(text="Выберите тип подписки:", reply_markup=women_inline)

    elif gender == 'Мужчина':
        await callback_query.message.delete()
        keyboard = ReplyKeyboardMarkup(keyboard=prev_next_button, resize_keyboard=True, one_time_keyboard=False)

        with SessionManager() as db:
            profiles = get_all_profiles(db=db, city=city)

        if not profiles:
            inline_other_city = InlineKeyboardMarkup(inline_keyboard=other_city)
            await callback_query.message.answer("Анкет в вашем городе ещё нет", reply_markup=inline_other_city)
            return

        random_profile = random.choice(profiles)

        service_info = []
        if random_profile.apartments:
            service_info.append("Принимаю в апартаментах")
        if random_profile.outcall:
            service_info.append("Работаю на выезд")
        service_text = " и ".join(service_info).capitalize()

        photos_paths = [f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{random_profile.user_id}_{i}.jpg" for i in range(1, 4) if os.path.exists(f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{random_profile.user_id}_{i}.jpg")]
        if photos_paths:
            media = [InputMediaPhoto(media=FSInputFile(path=photo_path),
                                     caption=f"<b>Имя:</b> {random_profile.name}\n"
                                             f"<b>Возраст:</b> {random_profile.age}\n"
                                             f"<b>Вес:</b> {random_profile.weight}\n"
                                             f"<b>Рост:</b> {random_profile.height}\n"
                                             f"<b>Размер груди:</b> {random_profile.breast_size}\n"
                                             f"<b>Стоимость за час:</b> {random_profile.hourly_rate} руб\n\n"
                                             f"{service_text if service_text else 'Услуги не указаны'}\n\n"
                                             f"<b>Номер телефона:</b> <tg-spoiler>{random_profile.phone_number}</tg-spoiler>")
                     for photo_path in photos_paths]
            await callback_query.message.answer_media_group(media)
        else:
            await callback_query.message.answer(
                text=f"<b>Имя:</b> {random_profile.name}\n"
                     f"<b>Возраст:</b> {random_profile.age}\n"
                     f"<b>Вес:</b> {random_profile.weight}\n"
                     f"<b>Рост:</b> {random_profile.height}\n"
                     f"<b>Размер груди:</b> {random_profile.breast_size}\n"
                     f"<b>Стоимость за час:</b> {random_profile.hourly_rate} руб\n\n"
                     f"{service_text if service_text else 'Услуги не указаны'}\n\n"
                     f"<b>Номер телефона:</b> <tg-spoiler>{random_profile.phone_number}</tg-spoiler>",
                reply_markup=keyboard
            )
