import asyncio
import logging
from datetime import datetime, timedelta

import aiohttp
from aiogram import Router, F
from aiogram.types import (CallbackQuery,
                           InlineKeyboardButton,
                           InlineKeyboardMarkup)

from app.database.models.users import async_session_maker
from app.database.requests.crud import (get_user_info,
                                        update_user_subscription)

from itsdangerous import URLSafeTimedSerializer

tinkoff_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = async_session_maker()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()


SECRET_KEY = 'venz2001'
SALT = 'venyapopov'


def generate_payment_token(user_id, amount):
    """
    Генерация токена с id юзера и ценой подписки внутри токена.
    Добавлена для шифровки данных в url.
    """
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    token = serializer.dumps({'user_id': user_id, 'amount': amount},
                             salt=SALT)
    return token


def verify_payment_token(token):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        data = serializer.loads(token, salt=SALT)
        return data
    except Exception as e:
        logging.error(f"Invalid token: {e}")
        return None


async def check_payment(token):
    """
    Проверка платежа, если пользователь успешно оплатил.
    Запрос идет на наш FastAPI сервер.
    """
    url = "https://black-fox1.ru/pay"
    data = verify_payment_token(token)

    if data is None:
        return False

    user_id = data['user_id']

    params = {'AccountId': user_id}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, ssl=False) as response:
                if response.status == 200:
                    response_data = await response.json()
                    for transaction in response_data:
                        if transaction.get('AccountId') == str(user_id) and transaction.get('Status') == 'Completed':
                            return True
    except Exception as e:
        logging.error(f"Error during payment check: {e}")
    return False


current_payment_tasks = {}


async def periodic_payment_check(user_id,
                                 subscription_type,
                                 callback_query: CallbackQuery):
    """
    Проверка платежа каждые 10 секунд в течение 3 минут после выбора подписки.
    """
    try:
        start_time = datetime.now()
        timeout = timedelta(minutes=3)

        while True:
            if datetime.now() - start_time > timeout:
                await callback_query.message.answer(text="Не удалось "
                                                         "оплатить. Время ожидания истекло.")
                break

            payment_successful = await check_payment(user_id)
            if payment_successful:
                async with SessionManager() as db:
                    await update_user_subscription(
                        db=db,
                        user_id=user_id,
                        subscription_status="True",
                        subscription_type=subscription_type,
                        subscription_end_date=datetime.now() + timedelta(days=30)
                    )
                await callback_query.message.answer(text="Подписка успешно оформлена.\n\n"
                                                         "Присоединяйтесь в наш чат "
                                                         "https://t.me/eskort555")
                break
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        raise


@tinkoff_router.callback_query(F.data.startswith('subscribe_'))
async def process_subscription(callback_query: CallbackQuery):
    """
    Обработка кнопки подписки, в зависимости от подписки из нее вытаскивается тип и цена
    для дальнейшей оплаты.
    """
    try:
        await callback_query.message.delete()
        subscription_map = {
            "subscribe_999_check": (999, "Проверка"),
            "subscribe_1500_questionnaire": (1500, "Анкета"),
            "subscribe_999_check_and_questionnaire": (999, "Проверка + Анкета")
        }

        callback_data = callback_query.data

        # Получаем сумму и описание
        amount, description = subscription_map.get(callback_data, (None, None))

        if amount is None or description is None:
            await callback_query.message.answer("Некорректный тип подписки.")
            return

        user_id = callback_query.from_user.id

        if user_id in current_payment_tasks:
            current_payment_tasks[user_id].cancel()

        # Генерация токена
        token = generate_payment_token(user_id, amount)
        payment_url = f"https://black-fox1.ru/payment?token={token}"

        payment_button = [
            [
                InlineKeyboardButton(text="Оплатить", url=payment_url)
            ]
        ]

        pay_url = InlineKeyboardMarkup(inline_keyboard=payment_button)

        await callback_query.message.answer(text="Ваша ссылка на оплату подписки👇",
                                            reply_markup=pay_url)

        payment_task = asyncio.create_task(periodic_payment_check(user_id,
                                                                  description,
                                                                  callback_query))
        current_payment_tasks[user_id] = payment_task

        try:
            await asyncio.wait_for(payment_task, timeout=3 * 60)
        except asyncio.TimeoutError:
            await callback_query.message.answer(text="Не удалось оплатить. "
                                                     "Время ожидания истекло.")
            payment_task.cancel()
    except Exception as e:
        logging.error(f"Error during subscription process: {e}")


async def update_subscription_in_db(account_id):
    """
    Обновление записи в БД при неуспешной оплате.
    """
    async with SessionManager() as db:
        user = await get_user_info(db, account_id)
        if user:
            await update_user_subscription(
                db=db,
                user_id=account_id,
                subscription_status="False",
                subscription_type="None",
                subscription_end_date=datetime.now()
            )
            await db.commit()
            return True
    return False


async def daily_subscription_check():
    """
    Периодическая проверка платежей по рекуррентным платежам.
    При неуспешных автоплатежах отмена подписки.
    """
    url = "https://black-fox1.ru/recurrent"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    for subscription in data:
                        model = subscription.get('Model', {})
                        account_id = model.get('AccountId')
                        status = model.get('Status')

                        if status in ['Cancelled', 'Rejected', 'Expired']:
                            updated = await update_subscription_in_db(account_id)
                            if updated:
                                logging.info(f"Subscription status updated for "
                                             f"AccountId: {account_id}")
                        else:
                            logging.info(f"Ignored subscription with AccountId "
                                         f"{account_id}, Status: {status}")
                else:
                    logging.error(f"Failed to fetch subscriptions data. "
                                  f"Status code: {response.status}")
    except Exception as e:
        logging.error(f"Error during daily subscription check: {e}")


async def schedule_daily_subscription_check():
    while True:
        await daily_subscription_check()
        await asyncio.sleep(24 * 60 * 60)




