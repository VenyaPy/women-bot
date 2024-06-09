import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from app.handlers.admin.admin_mailing import admin_mailing_router
from app.handlers.admin.admin_start import admin_router
from app.handlers.user.men_menu import men_router
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
                   admin_mailing_router)


async def main() -> None:
    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())
