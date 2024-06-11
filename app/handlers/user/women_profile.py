import os
import re
from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.exc import SQLAlchemyError
from app.database.models.users import SessionLocal
from app.database.requests.crud import get_user_info, get_user_city, create_profile, is_profile_info, delete_profile
from app.templates.keyboards.inline_buttons import women_subscribe, enough_photo_women, girl_profile_choose

women_profile_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


@women_profile_router.callback_query(F.data == "del_my_profile")
async def delete_my_profile_from_bd(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    with SessionManager() as db:
        delete_profile(db=db, user_id=user_id)


    await callback_query.message.answer(text="Ваша анкета удалена! Теперь вы можете добавить новую.")



class WomenProfile(StatesGroup):
    name = State()
    age = State()
    weight = State()
    height = State()
    breast_size = State()
    hourly_rate = State()
    apartments = State()
    outcall = State()
    photo1 = State()
    photo2 = State()
    photo3 = State()
    phone_number = State()


@women_profile_router.message(F.text == "Добавить анкету")
async def add_women_profile(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id

        inline_girl_del = InlineKeyboardMarkup(inline_keyboard=girl_profile_choose)

        with SessionManager() as db:
            info = get_user_info(db=db, user_id=user_id)
            is_profile = is_profile_info(db=db, user_id=user_id)

        sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)

        if info.subscription_type not in ["Анкета", "Проверка + Анкета"]:
            await message.answer(text="Чтобы воспользоваться этой функцией необходимо оформить подписку:", reply_markup=sub_inline)
            return

        if is_profile:
            service_info = []
            if is_profile.apartments:
                service_info.append("Принимаю в апартаментах")
            if is_profile.outcall:
                service_info.append("Работаю на выезд")
            service_text = " и ".join(service_info).capitalize()

            photos_paths = [f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{is_profile.user_id}_{i}.jpg" for i in range(1, 4) if os.path.exists(f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{is_profile.user_id}_{i}.jpg")]
            if photos_paths:
                media = [InputMediaPhoto(media=FSInputFile(path=photo_path), caption=f"<b>Имя:</b> {is_profile.name}\n<b>Возраст:</b> {is_profile.age}\n<b>Вес:</b> {is_profile.weight}\n<b>Рост:</b> {is_profile.height}\n<b>Размер груди:</b> {is_profile.breast_size}\n<b>Стоимость за час:</b> {is_profile.hourly_rate} руб\n\n{service_text if service_text else 'Услуги не указаны'}\n\n<b>Номер телефона:</b> <tg-spoiler>{is_profile.phone_number}</tg-spoiler>") for photo_path in photos_paths]
                await message.answer_media_group(media)
                await message.answer(text="Действия с анкетой:", reply_markup=inline_girl_del)
            else:
                await message.answer(text=f"<b>Имя:</b> {is_profile.name}\n<b>Возраст:</b> {is_profile.age}\n<b>Вес:</b> {is_profile.weight}\n<b>Рост:</b> {is_profile.height}\n<b>Размер груди:</b> {is_profile.breast_size}\n<b>Стоимость за час:</b> {is_profile.hourly_rate} руб\n\n{service_text if service_text else 'Услуги не указаны'}\n\n<b>Номер телефона:</b> <tg-spoiler>{is_profile.phone_number}</tg-spoiler>", reply_markup=inline_girl_del)
        else:
            await state.set_state(WomenProfile.name)
            await message.answer("Введите ваше имя, например: Ирина")
    except Exception as e:
        await message.answer("Произошла ошибка при добавлении профиля. Попробуйте еще раз.")
        print(f"Error in add_profile: {e}")


@women_profile_router.message(WomenProfile.name)
async def process_name(message: Message, state: FSMContext):
    try:
        await state.update_data(name=message.text)
        await message.answer("Введите ваш возраст, например: 25")
        await state.set_state(WomenProfile.age)
    except Exception as e:
        print(e)


@women_profile_router.message(WomenProfile.age)
async def process_age(message: Message, state: FSMContext):
    try:
        if message.text.isdigit():
            await state.update_data(age=int(message.text))
            await message.answer("Введите ваш вес в кг, например: 55")
            await state.set_state(WomenProfile.weight)
        else:
            await message.answer("Введите возраст цифрами, например: 25")
    except Exception as e:
        print(e)


@women_profile_router.message(WomenProfile.weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        if message.text.isdigit():
            await state.update_data(weight=int(message.text))
            await message.answer("Введите ваш рост в см, например: 165")
            await state.set_state(WomenProfile.height)
        else:
            await message.answer("Введите вес цифрами в кг, например: 55")
    except Exception as e:
        print(e)


@women_profile_router.message(WomenProfile.height)
async def process_height(message: Message, state: FSMContext):
    try:
        if message.text.isdigit():
            await state.update_data(height=int(message.text))
            await message.answer("Введите размер груди, например: 2")
            await state.set_state(WomenProfile.breast_size)
        else:
            await message.answer("Введите рост цифрами в см, например: 170")
    except Exception as e:
        print(e)


@women_profile_router.message(WomenProfile.breast_size)
async def process_breast_size(message: Message, state: FSMContext):
    try:
        if message.text.isdigit():
            await state.update_data(breast_size=message.text)
            await message.answer("Введите вашу цену за час в рублях, например: 2000")
            await state.set_state(WomenProfile.hourly_rate)
        else:
            await message.answer("Введите размер груди цифрами, например: 2")
    except Exception as e:
        print(e)


@women_profile_router.message(WomenProfile.hourly_rate)
async def process_hourly_rate(message: Message, state: FSMContext):
    try:
        if message.text.isdigit():
            await state.update_data(hourly_rate=int(message.text))
            await message.answer("Введите ваш номер телефона в формате: 8 *** *** ** **")
            await state.set_state(WomenProfile.phone_number)
        else:
            await message.answer("Введите цену за час цифрами, например: 2000")
    except Exception as e:
        print(e)


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
    try:
        formatted_number = format_phone_number(message.text)
        if "Ошибка" in formatted_number:
            await message.answer(formatted_number)
        else:
            await state.update_data(phone_number=formatted_number)
            await message.answer(f"Принимаете в апартаментах? Ответьте 'Да' или 'Нет'")
            await state.set_state(WomenProfile.apartments)
    except Exception as e:
        print(e)


@women_profile_router.message(WomenProfile.apartments)
async def process_apartments(message: Message, state: FSMContext):
    try:
        if message.text.lower() in ['да', 'нет']:
            await state.update_data(apartments=message.text.lower())
            await message.answer("Работаете ли на выезд?\n\nОтветьте 'Да' или 'Нет'")
            await state.set_state(WomenProfile.outcall)
        else:
            await message.answer("Ответьте 'Да' или 'Нет'")
    except Exception as e:
        print(e)


@women_profile_router.message(WomenProfile.outcall)
async def process_outcall(message: Message, state: FSMContext):
    try:
        if message.text.lower() in ['да', 'нет']:
            await state.update_data(outcall=message.text.lower())
            await message.answer("Пожалуйста, загрузите первое фото.")
            await state.set_state(WomenProfile.photo1)
        else:
            await message.answer("Ответьте 'Да' или 'Нет'")
    except Exception as e:
        print(e)


@women_profile_router.message(WomenProfile.photo1, F.photo)
async def process_photo1(message: Message, state: FSMContext):
    user_data = await state.get_data()
    photos_list = user_data.get("photos", [])
    inline_done_photo = InlineKeyboardMarkup(inline_keyboard=enough_photo_women)

    try:
        largest_photo = message.photo[-1]
        photo_file_id = largest_photo.file_id
        file_path = f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{message.from_user.id}_{len(photos_list) + 1}.jpg"
        await message.bot.download(file=photo_file_id, destination=file_path)
        photos_list.append(file_path)

        await state.update_data(photos=photos_list)

        await message.answer("Загрузите еще одно фото или подтвердите анкету.", reply_markup=inline_done_photo)
        await state.set_state(WomenProfile.photo2)

    except Exception as e:
        await message.answer("Произошла ошибка при загрузке фотографии. Попробуйте еще раз.")
        print(f"Error processing photo1: {e}")


@women_profile_router.message(WomenProfile.photo2, F.photo)
async def process_photo2(message: Message, state: FSMContext):
    user_data = await state.get_data()
    photos_list = user_data.get("photos", [])
    inline_done_photo = InlineKeyboardMarkup(inline_keyboard=enough_photo_women)

    try:
        largest_photo = message.photo[-1]
        photo_file_id = largest_photo.file_id
        file_path = f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{message.from_user.id}_{len(photos_list) + 1}.jpg"
        await message.bot.download(file=photo_file_id, destination=file_path)
        photos_list.append(file_path)

        await state.update_data(photos=photos_list)

        await message.answer("Загрузите еще одно фото или подтвердите анкету.", reply_markup=inline_done_photo)
        await state.set_state(WomenProfile.photo3)

    except Exception as e:
        await message.answer("Произошла ошибка при загрузке фотографии. Попробуйте еще раз.")
        print(f"Error processing photo2: {e}")


@women_profile_router.message(WomenProfile.photo3, F.photo)
async def process_photo3(message: Message, state: FSMContext):
    user_data = await state.get_data()
    photos_list = user_data.get("photos", [])
    inline_done_photo = InlineKeyboardMarkup(inline_keyboard=enough_photo_women)

    try:
        largest_photo = message.photo[-1]
        photo_file_id = largest_photo.file_id
        file_path = f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{message.from_user.id}_{len(photos_list) + 1}.jpg"
        await message.bot.download(file=photo_file_id, destination=file_path)
        photos_list.append(file_path)

        await state.update_data(photos=photos_list)

        await message.answer("Подтвердите анкету.", reply_markup=inline_done_photo)

    except Exception as e:
        await message.answer("Произошла ошибка при загрузке фотографии. Попробуйте еще раз.")
        print(f"Error processing photo3: {e}")


@women_profile_router.callback_query(F.data == "enough_photos")
async def send_women_profile_to_bd(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    try:
        with SessionManager() as db:
            city = get_user_city(db=db, user_id=callback_query.from_user.id)
            create_profile(
                db=db,
                user_id=callback_query.from_user.id,
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

            service_info = []
            if data.get("apartments", "").lower() == "да":
                service_info.append("Принимаю в апартаментах")
            if data.get("outcall", "").lower() == "да":
                service_info.append("Работаю на выезд")
            service_text = " и ".join(service_info).capitalize()

            photos_paths = [f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{callback_query.from_user.id}_{i}.jpg" for i in range(1, 4) if os.path.exists(f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{callback_query.from_user.id}_{i}.jpg")]
            if photos_paths:
                media = [InputMediaPhoto(media=FSInputFile(path=photo_path),
                                         caption=f"<b>Имя:</b> {data.get('name')}\n<b>Возраст:</b> {data.get('age')}\n"
                                                 f"<b>Вес:</b> {data.get('weight')}\n<b>Рост:</b> {data.get('height')}\n"
                                                 f"<b>Размер груди:</b> {data.get('breast_size')}\n"
                                                 f"<b>Стоимость за час:</b> {data.get('hourly_rate')} руб\n\n"
                                                 f"{service_text if service_text else 'Услуги не указаны'}\n\n"
                                                 f"<b>Номер телефона:</b> {data.get('phone_number')}")
                         for photo_path in photos_paths]
                await callback_query.message.answer(text="Вот как выглядит ваша анкета 👇")
                await callback_query.message.answer_media_group(media)

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
    try:
        user_id = callback_query.from_user.id
        base_path = f"/Users/venya/PycharmProjects/women-bot/app/database/photos/{user_id}"

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
        await callback_query.message.answer("Произошла ошибка при отмене анкеты. Попробуйте еще раз.")
        print(f"Error in cancel_send_profile: {e}")

