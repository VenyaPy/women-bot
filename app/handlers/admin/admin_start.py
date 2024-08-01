from aiogram import Router
from aiogram.types import (Message,
                           ReplyKeyboardMarkup)
from app.filters.chat_types import IsAdmin
from aiogram.filters import Command

from app.templates.keyboards.keyboard_buttons import admin_menu_keyboard

admin_router = Router()
admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())


@admin_router.message(Command('start_admin'))
async def admin_start_menu(message: Message):
    """
    Начальное меню администратора
    """
    reply_markup_admin = ReplyKeyboardMarkup(keyboard=admin_menu_keyboard,
                                             resize_keyboard=True,
                                             one_time_keyboard=False)
    await message.answer(
        text="Добро пожаловать в админ-меню!\n\nТвои функции👇",
        reply_markup=reply_markup_admin
    )