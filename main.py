import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.handlers.admin.admin_cancel import admin_cancel_router
from app.handlers.admin.admin_mailing import admin_mailing_router
from app.handlers.admin.admin_start import admin_router
from app.handlers.user.men_menu import men_router
from app.handlers.user.tinkoff_user_pay import tinkoff_router, schedule_daily_subscription_check
from config import TOKEN_BOT
from aiogram.client.default import DefaultBotProperties
from app.handlers.user.start import start_router
from app.handlers.user.women_help import women_router
from app.handlers.user.women_review import women_review_router
from app.handlers.user.women_check_number import women_check_router
from app.handlers.user.women_profile import women_profile_router


TOKEN = TOKEN_BOT
bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

dp.include_routers(start_router,
                   women_router,
                   women_review_router,
                   women_check_router,
                   women_profile_router,
                   men_router,
                   admin_router,
                   admin_mailing_router,
                   tinkoff_router,
                   admin_cancel_router)


async def main() -> None:
    await dp.start_polling(bot)
    await schedule_daily_subscription_check()


if __name__ == "__main__":
    asyncio.run(main())
