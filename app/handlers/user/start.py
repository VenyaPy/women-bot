from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup

from app.database.models.users import SessionLocal, User
from app.database.requests.crud import add_or_update_user, update_user_city, get_all_profiles, get_user_info
from app.templates.keyboards.keyboard_buttons import prev_next_button, reviews_button
from app.templates.keyboards.inline_buttons import gender_start, city_choose, women_subscribe, politic_buttons
from app.templates.texts.user import message_command_start

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

    with SessionManager() as db:
        is_user = get_user_info(db=db, user_id=message.from_user.id)

    if is_user:
        await message.answer(text=message_command_start, reply_markup=inline_politics)

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


@start_router.callback_query(lambda c: c.data.startswith('city_'))
async def process_city_selection(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    city_data = callback_query.data
    city = city_data.split('_', 1)[1]

    with SessionManager() as db:
        update_user_city(db=db, user_id=user_id, city=city)

    with SessionManager() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        gender = user.gender if user else None

    if gender == 'Женщина':
        await callback_query.message.delete()
        women_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)
        name = callback_query.from_user.first_name
        women_review = ReplyKeyboardMarkup(keyboard=reviews_button,
                                           resize_keyboard=True,
                                           one_time_keyboard=False)

        await callback_query.message.answer(text=f"Привет, {name}", reply_markup=women_review)
        await callback_query.message.answer(text="Выберите тип подписки:",
                                            reply_markup=women_inline)
    elif gender == 'Мужчина':
        await callback_query.message.delete()
        keyboard = ReplyKeyboardMarkup(keyboard=prev_next_button,
                                       resize_keyboard=True,
                                       one_time_keyboard=False)
        profile = get_all_profiles(db=db, city=city)

        if profile:
            service_info = []
            if profile.apartments:
                service_info.append("принимаю в апартаментах")
            if profile.outcall:
                service_info.append("работаю на выезд")
            service_text = " и ".join(service_info)

            await callback_query.message.answer(
                text=f'''
                Имя: {profile.name}
                Возраст: {profile.age}
                Вес: {profile.weight}
                Рост: {profile.height}
                Размер груди: {profile.breast_size}
                Стоимость за час: {profile.hourly_rate}
                {service_text if service_text else ''}
                ''',
                reply_markup=keyboard
            )
        else:
            await callback_query.message.answer(text="Анкет в вашем городе ещё нет",
                                                reply_markup=keyboard)


