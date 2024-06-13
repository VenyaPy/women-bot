from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    CallbackQuery, InlineKeyboardButton
)

from app.database.models.users import AsyncSession, async_session_maker
from app.database.requests.crud import get_users_with_active_subscription, get_female_users, get_male_users, \
    get_all_user_ids
from app.filters.chat_types import IsAdmin
from app.templates.keyboards.inline_buttons import users_of_mailing, is_check_post, send_or_delete_mail


class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = async_session_maker()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()


admin_mailing_router = Router()
admin_mailing_router.message.filter(IsAdmin())
admin_mailing_router.callback_query.filter(IsAdmin())


@admin_mailing_router.message(F.text.lower() == "рассылка")
async def newsletter_menu(message: Message, state: FSMContext):
    try:
        await state.clear()
        reply = InlineKeyboardMarkup(inline_keyboard=users_of_mailing)
        await message.answer(text="<b>📨 Меню постинга</b>\n\nТы можешь сделать рассылку пользователям 👇", reply_markup=reply)
    except Exception as e:
        print(f"Ошибка в newsletter_menu: {e}")


class Form(StatesGroup):
    add_text = State()
    ask_add_media = State()
    add_photo = State()
    send_post = State()


@admin_mailing_router.callback_query(F.data.in_({"send_to_all", "send_mail_to_mens", "send_mail_to_women", "send_mail_to_subscribers"}))
async def select_recipients(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.message.delete()
        await state.update_data(recipient_category=callback.data)
        await state.set_state(Form.add_text)
        await callback.message.answer(text="👇 Введите текст будущего поста 👇")
    except Exception as e:
        print(f"Ошибка в select_recipients: {e}")


@admin_mailing_router.message(Form.add_text)
async def process_text(message: Message, state: FSMContext) -> None:
    try:
        await state.update_data(add_text=message.html_text, add_entities=message.entities)
        await state.set_state(Form.ask_add_media)
        inline_add_media = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Добавить фото или видео", callback_data="add_media")],
            [InlineKeyboardButton(text="Не добавлять", callback_data="no_media")]
        ])
        await message.answer("Хотите добавить фото или видео?", reply_markup=inline_add_media)
    except Exception as e:
        print(f"Ошибка в process_text: {e}")


@admin_mailing_router.callback_query(Form.ask_add_media, F.data == "add_media")
async def ask_add_media(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.message.delete()
        await state.set_state(Form.add_photo)
        await callback.message.answer("Теперь добавьте фото или видео к посту")
    except Exception as e:
        print(f"Ошибка в ask_add_media: {e}")


@admin_mailing_router.callback_query(Form.ask_add_media, F.data == "no_media")
async def no_add_media(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.message.delete()
        data = await state.get_data()
        await finish_post_creation(callback, state)
    except Exception as e:
        print(f"Ошибка в no_add_media: {e}")


@admin_mailing_router.message(Form.add_photo)
async def process_photo(message: Message, state: FSMContext) -> None:
    try:
        inline_results = InlineKeyboardMarkup(inline_keyboard=is_check_post)

        if message.photo:
            media_file_id = message.photo[-1].file_id
            media_type = 'photo'
        elif message.video:
            media_file_id = message.video.file_id
            media_type = 'video'
        else:
            await message.answer("Пожалуйста, отправьте фото или видео.")
            return

        await state.update_data(add_media=media_file_id, media_type=media_type)
        await message.answer('Пост готов!', reply_markup=inline_results)
    except Exception as e:
        print(f"Ошибка в process_photo: {e}")


@admin_mailing_router.callback_query(F.data == "check_mailing_result")
async def finish_post_creation(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        data = await state.get_data()
        add_text = data.get("add_text", "")
        add_media = data.get("add_media", "")
        media_type = data.get("media_type", "")
        entities = data.get("add_entities", [])

        if media_type:
            if media_type == 'photo':
                await callback.message.answer_photo(photo=add_media, caption=add_text, caption_entities=entities)
            elif media_type == 'video':
                await callback.message.answer_video(video=add_media, caption=add_text, caption_entities=entities)
        else:
            await callback.message.answer(text=add_text, entities=entities)

        done_b = InlineKeyboardMarkup(inline_keyboard=send_or_delete_mail)
        await callback.message.answer(text="Что делаем с постом?", reply_markup=done_b)
        await state.set_state(Form.send_post)
    except Exception as e:
        print(f"Ошибка в finish_post_creation: {e}")


@admin_mailing_router.callback_query(F.data == 'delete_mail')
async def cancel_handler(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        current_state = await state.get_state()
        if current_state is None:
            return
        await state.clear()
        await callback.message.answer("Пост удален")
    except Exception as e:
        print(f"Ошибка в cancel_handler: {e}")


@admin_mailing_router.callback_query(F.data == 'send_mail')
async def send_post(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        data = await state.get_data()
        add_text = data.get("add_text", "")
        add_media = data.get("add_media", "")
        media_type = data.get("media_type", "")
        recipient_category = data.get("recipient_category", "")
        entities = data.get("add_entities", [])

        user_ids = []

        async with SessionManager() as db:
            if recipient_category == "send_to_all":
                user_ids = await get_all_user_ids(db)
            elif recipient_category == "send_mail_to_mens":
                user_ids = [user.user_id for user in await get_male_users(db)]
            elif recipient_category == "send_mail_to_women":
                user_ids = [user.user_id for user in await get_female_users(db)]
            elif recipient_category == "send_mail_to_subscribers":
                user_ids = [user.user_id for user in await get_users_with_active_subscription(db)]

        successful_sends = 0
        failed_sends = 0

        for user_id in user_ids:
            try:
                if media_type == 'photo':
                    await callback.bot.send_photo(chat_id=user_id, photo=add_media, caption=add_text, caption_entities=entities)
                elif media_type == 'video':
                    await callback.bot.send_video(chat_id=user_id, video=add_media, caption=add_text, caption_entities=entities)
                else:
                    await callback.bot.send_message(chat_id=user_id, text=add_text, entities=entities)
                successful_sends += 1
            except Exception as e:
                print(f"Не удалось отправить пост пользователю {user_id}: {e}")
                failed_sends += 1

        await callback.message.answer(f"Рассылка завершена. Успешно: {successful_sends}, Неудачно: {failed_sends}")
    except Exception as e:
        print(f"Ошибка в send_post: {e}")
    finally:
        await state.clear()
