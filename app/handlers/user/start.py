import os
import random
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, InputMediaPhoto, FSInputFile, InlineKeyboardButton
from sqlalchemy import select

from app.database.models.users import User, async_session_maker
from app.database.requests.crud import add_or_update_user, update_user_city, get_all_profiles, get_user_info, get_user_city, is_profile_info
from app.handlers.admin.admin_start import admin_start_menu
from app.templates.keyboards.keyboard_buttons import prev_next_button, reviews_button, reviews_button_delete
from app.templates.keyboards.inline_buttons import gender_start, city_choose, women_subscribe, politic_buttons, other_city, read_faq_inline
from app.templates.texts.user import message_command_start, faq
from config import ADMINS

start_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = async_session_maker()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()


async def confirm_subscribe(message: Message):
    try:
        await message.answer(
            "Соглашаюсь с "
            "<a href='https://telegra.ph/Politika-konfidencialnosti-06-12-11'>Политикой конфиденциальности</a> и "
            "<a href='https://telegra.ph/Oferta-06-12-2'>Офертой</a>.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Да", callback_data="user_agree")],
                [InlineKeyboardButton(text="Нет", callback_data="user_disagree")]
            ])
        )
    except Exception as e:
        print(f"Ошибка при согласии с офертами: {e}")


@start_router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    try:
        if user_id in ADMINS:
            await admin_start_menu(message)
        else:
            await confirm_subscribe(message)
    except Exception as e:
        print(f"Ошибка в функции старт: {e}")


@start_router.callback_query(F.data == "user_agree")
async def user_agree(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        await callback_query.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    try:
        async with SessionManager() as db:
            is_user = await get_user_info(db=db, user_id=user_id)
            city = await get_user_city(db=db, user_id=user_id)
    except Exception as e:
        print(f"Ошибка при получении информации о пользователе: {e}")
        return

    try:
        if is_user and is_user.gender == "Мужчина":
            keyboard = ReplyKeyboardMarkup(keyboard=prev_next_button,
                                           resize_keyboard=True,
                                           one_time_keyboard=False)

            try:
                async with SessionManager() as db:
                    profiles = await get_all_profiles(db=db, city=city)
            except Exception as e:
                print(f"Ошибка при получении всех профилей: {e}")
                return

            if not profiles:
                inline_other_city = InlineKeyboardMarkup(inline_keyboard=other_city)
                try:
                    await callback_query.message.answer("Анкет в вашем городе ещё нет", reply_markup=inline_other_city)
                except Exception as e:
                    print(f"Ошибка при отправке сообщения о нехватке анкет: {e}")
                return

            random_profile = random.choice(profiles)

            service_info = []
            if random_profile.apartments:
                service_info.append("Принимаю в апартаментах")
            if random_profile.outcall:
                service_info.append("Работаю на выезд")
            service_text = " и ".join(service_info).capitalize()

            photos_paths = [f"/home/women-bot/app/database/photos/{random_profile.user_id}_{i}.jpg" for i in range(1, 4) if os.path.exists(f"/home/women-bot/app/database/photos/{random_profile.user_id}_{i}.jpg")]
            if photos_paths:
                media = [
                    InputMediaPhoto(
                        media=FSInputFile(path=photo_path),
                        caption=(
                            f"<b>Имя:</b> {random_profile.name}\n"
                            f"<b>Возраст:</b> {random_profile.age}\n"
                            f"<b>Вес:</b> {random_profile.weight}\n"
                            f"<b>Рост:</b> {random_profile.height}\n"
                            f"<b>Размер груди:</b> {random_profile.breast_size}\n\n"
                            f"<b>Номер телефона:</b> <tg-spoiler>{random_profile.phone_number}</tg-spoiler>"
                        ) if idx == 0 else None  # Подпись только для первой фотографии
                    )
                    for idx, photo_path in enumerate(photos_paths)
                ]

                try:
                    await callback_query.message.answer_media_group(media)
                    await callback_query.message.answer(
                        text="Подсказка! Вы можете использовать стрелки на клавиатуре для переключения между анкетами.",
                        reply_markup=keyboard
                    )
                except Exception as e:
                    print(f"Ошибка при отправке медиагруппы или сообщения: {e}")

            else:
                try:
                    await callback_query.message.answer(
                        text=f"<b>Имя:</b> {random_profile.name}\n"
                             f"<b>Возраст:</b> {random_profile.age}\n"
                             f"<b>Вес:</b> {random_profile.weight}\n"
                             f"<b>Рост:</b> {random_profile.height}\n"
                             f"<b>Размер груди:</b> {random_profile.breast_size}\n\n"
                             f"\n\n<b>Номер телефона:</b> <tg-spoiler>{random_profile.phone_number}</tg-spoiler>",
                        reply_markup=keyboard
                    )
                except Exception as e:
                    print(f"Ошибка при отправке сообщения о профиле: {e}")

        if is_user and is_user.gender == "Женщина":
            try:
                async with SessionManager() as db:
                    is_profile = await is_profile_info(db=db, user_id=user_id)
            except Exception as e:
                print(f"Ошибка при проверке информации о профиле: {e}")
                return

            try:
                if is_profile:
                    women_key_del = ReplyKeyboardMarkup(keyboard=reviews_button_delete, resize_keyboard=True,
                                                        one_time_keyboard=False)
                    await callback_query.message.answer(text=message_command_start, reply_markup=women_key_del)
                else:
                    women_review = ReplyKeyboardMarkup(keyboard=reviews_button, resize_keyboard=True, one_time_keyboard=False)
                    await callback_query.message.answer(text=message_command_start, reply_markup=women_review)
            except Exception as e:
                print(f"Ошибка при отправке сообщения для женщин: {e}")

        if not is_user:
            inline_politics = InlineKeyboardMarkup(inline_keyboard=politic_buttons)
            try:
                await callback_query.message.answer(text=message_command_start, reply_markup=inline_politics)
                inline_gender = InlineKeyboardMarkup(inline_keyboard=gender_start)
                await callback_query.message.answer(text="Выберите ваш пол:", reply_markup=inline_gender)
            except Exception as e:
                print(f"Ошибка при отправке сообщений для нового пользователя: {e}")
    except Exception as e:
        print(f"Ошибка в основной части функции user_agree: {e}")


@start_router.callback_query(F.data == "user_disagree")
async def user_disagree(callback_query: CallbackQuery):
    try:
        await callback_query.message.answer("Вы не можете пользоваться ботом без согласия на обработку данных.")
        await confirm_subscribe(callback_query.message)
    except Exception as e:
        print(f"Ошибка при отказе пользователя: {e}")


@start_router.callback_query(F.data == "faq_reader")
async def text_faq_instr(callback_query: CallbackQuery):
    try:
        await callback_query.message.answer(text=faq)
    except Exception as e:
        print(f"Ошибка при отправке FAQ: {e}")


@start_router.callback_query(F.data.in_({"man_gender", "woman_gender"}))
async def process_gender_selection(callback_query: CallbackQuery):
    try:
        await callback_query.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения выбора пола: {e}")

    user_id = callback_query.from_user.id
    gender = 'Мужчина' if callback_query.data == 'man_gender' else 'Женщина'

    try:
        async with SessionManager() as db:
            await add_or_update_user(user_id=user_id, gender=gender, db=db)
    except Exception as e:
        print(f"Ошибка при добавлении или обновлении пользователя: {e}")

    city_inline = InlineKeyboardMarkup(inline_keyboard=city_choose)
    try:
        await callback_query.message.answer(text="Выберите свой город:", reply_markup=city_inline)
    except Exception as e:
        print(f"Ошибка при отправке сообщения выбора города: {e}")


@start_router.callback_query(F.data.startswith('city_'))
async def process_city_selection(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    city_data = callback_query.data
    city = city_data.split('_', 1)[1]

    try:
        async with SessionManager() as db:
            await update_user_city(db=db, user_id=user_id, city=city)
            result = await db.execute(select(User).filter(User.user_id == user_id))
            user = result.scalars().first()
            gender = user.gender if user else None
    except Exception as e:
        print(f"Ошибка при обновлении города пользователя: {e}")
        return

    try:
        if gender == 'Женщина':
            await callback_query.message.delete()
            women_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)
            name = callback_query.from_user.first_name
            women_review = ReplyKeyboardMarkup(keyboard=reviews_button, resize_keyboard=True, one_time_keyboard=False)

            try:
                await callback_query.message.answer(text=f"Привет, {name}", reply_markup=women_review)
                await callback_query.message.answer(
                    text="Выберите тип подписки (автоматически продлевается каждый месяц):",
                    reply_markup=women_inline
                )
            except Exception as e:
                print(f"Ошибка при отправке сообщения выбора подписки: {e}")

        elif gender == 'Мужчина':
            await callback_query.message.delete()
            keyboard_mens = ReplyKeyboardMarkup(keyboard=prev_next_button,
                                                resize_keyboard=True,
                                                one_time_keyboard=False)

            try:
                async with SessionManager() as db:
                    profiles = await get_all_profiles(db=db, city=city)
            except Exception as e:
                print(f"Ошибка при получении всех профилей: {e}")
                return

            if not profiles:
                inline_other_city = InlineKeyboardMarkup(inline_keyboard=other_city)
                try:
                    await callback_query.message.answer("Анкет в вашем городе ещё нет", reply_markup=inline_other_city)
                except Exception as e:
                    print(f"Ошибка при отправке сообщения о нехватке анкет: {e}")
                return

            random_profile = random.choice(profiles)

            service_info = []
            if random_profile.apartments:
                service_info.append("Принимаю в апартаментах")
            if random_profile.outcall:
                service_info.append("Работаю на выезд")
            service_text = " и ".join(service_info).capitalize()

            photos_paths = [f"/Users/venya/women-bot/app/database/photos/{random_profile.user_id}_{i}.jpg" for i in range(1, 4) if os.path.exists(f"/home/women-bot/app/database/photos/{random_profile.user_id}_{i}.jpg")]
            if photos_paths:
                media = [
                    InputMediaPhoto(
                        media=FSInputFile(path=photo_path),
                        caption=(
                            f"<b>Имя:</b> {random_profile.name}\n"
                            f"<b>Возраст:</b> {random_profile.age}\n"
                            f"<b>Вес:</b> {random_profile.weight}\n"
                            f"<b>Рост:</b> {random_profile.height}\n"
                            f"<b>Размер груди:</b> {random_profile.breast_size}\n\n"
                            f"<b>Номер телефона:</b> <tg-spoiler>{random_profile.phone_number}</tg-spoiler>"
                        ) if idx == 0 else None
                    )
                    for idx, photo_path in enumerate(photos_paths)
                ]

                try:
                    await callback_query.message.answer_media_group(media)
                    await callback_query.message.answer(text="Подсказка! Вы можете использовать стрелки "
                                                             "на клавиатуре для переключения между анкетами.",
                                                        reply_markup=keyboard_mens)
                except Exception as e:
                    print(f"Ошибка при отправке медиагруппы или сообщения: {e}")
            else:
                try:
                    await callback_query.message.answer(
                        text=f"<b>Имя:</b> {random_profile.name}\n"
                             f"<b>Возраст:</b> {random_profile.age}\n"
                             f"<b>Вес:</b> {random_profile.weight}\n"
                             f"<b>Рост:</b> {random_profile.height}\n"
                             f"<b>Размер груди:</b> {random_profile.breast_size}\n\n"
                             f"\n\n<b>Номер телефона:</b> <tg-spoiler>{random_profile.phone_number}</tg-spoiler>",
                        reply_markup=keyboard_mens
                    )
                except Exception as e:
                    print(f"Ошибка при отправке сообщения о профиле: {e}")

    except Exception as e:
        print(f"Ошибка в основной части функции process_city_selection: {e}")
