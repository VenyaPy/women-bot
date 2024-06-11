import asyncio
import hashlib
import time
from datetime import datetime, timedelta

import aiohttp
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from app.database.models.users import SessionLocal, User
from app.database.requests.crud import get_user_info, update_user_subscription
from sqlalchemy.orm import Session

tinkoff_router = Router()

class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = SessionLocal()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

class TinkoffAPI:
    BASE_URL = "https://securepay.tinkoff.ru/v2/"

    def __init__(self, terminal_key, password):
        self.terminal_key = terminal_key
        self.password = password

    def generate_token(self, params, ordered_keys):
        params_with_password = params.copy()
        params_with_password['Password'] = self.password
        token_str = ''.join(str(params_with_password[key]) for key in ordered_keys if key in params_with_password)
        token = hashlib.sha256(token_str.encode('utf-8')).hexdigest()
        return token.lower()

    async def init_payment(self, amount, order_id, description, customer_key):
        url = self.BASE_URL + "Init"
        params = {
            "TerminalKey": self.terminal_key,
            "Amount": str(amount),
            "OrderId": order_id,
            "Description": description,
            "CustomerKey": customer_key,
            "Recurrent": "Y",
        }
        ordered_keys = ['Amount', 'CustomerKey', 'Description', 'OrderId', 'Password', 'Recurrent', 'TerminalKey']
        params["Token"] = self.generate_token(params, ordered_keys)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params, ssl=False) as response:
                    response_json = await response.json()
                    return response_json
        except aiohttp.ClientError as e:
            print(f"Error in init_payment: {e}")
            return {"Success": False, "Message": "Ошибка соединения с сервером оплаты"}

    async def get_payment_status(self, payment_id):
        url = self.BASE_URL + "GetState"
        params = {
            "TerminalKey": self.terminal_key,
            "PaymentId": payment_id,
            "Token": self.generate_token({
                "Password": self.password,
                "PaymentId": payment_id,
                "TerminalKey": self.terminal_key,
            }, ['Password', 'PaymentId', 'TerminalKey']),
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params, ssl=False) as response:
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error in get_payment_status: {e}")
            return {"Success": False, "Message": "Ошибка соединения с сервером оплаты"}

    async def charge_payment(self, payment_id, rebill_id):
        url = self.BASE_URL + "Charge"
        params = {
            "TerminalKey": self.terminal_key,
            "PaymentId": payment_id,
            "RebillId": rebill_id,
            "Token": self.generate_token({
                "Password": self.password,
                "PaymentId": payment_id,
                "RebillId": rebill_id,
                "TerminalKey": self.terminal_key,
            }, ['Password', 'PaymentId', 'RebillId', 'TerminalKey']),
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params, ssl=False) as response:
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error in charge_payment: {e}")
            return {"Success": False, "Message": "Ошибка соединения с сервером оплаты"}

tinkoff_api = TinkoffAPI(terminal_key="1717831041748DEMO", password="C^P0Gczux%x7otV#")

async def get_rebill_id(order_id, payment_id):
    url = "https://ve1.po2014.fvds.ru/v2/Notifications"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False) as response:
                data = await response.json()
                for item in data:
                    if item["OrderId"] == order_id or item["PaymentId"] == payment_id:
                        return item["RebillId"]
                return None
    except aiohttp.ClientError as e:
        print(f"Error in get_rebill_id: {e}")
        return None

async def check_payment_status_and_update_db(callback_query: CallbackQuery, payment_id, user_id, subscription_type):
    try:
        async with SessionManager() as db:
            user_info = get_user_info(db=db, user_id=user_id)
            if not user_info:
                await callback_query.message.answer("Не удалось найти информацию о пользователе.")
                return

            for _ in range(30):
                try:
                    payment_status_response = await tinkoff_api.get_payment_status(payment_id)
                    if payment_status_response["Success"]:
                        if payment_status_response["Status"] == "CONFIRMED":
                            await asyncio.sleep(5)  # Ждем 5 секунд перед запросом к серверу для получения rebill_id
                            rebill_id = await get_rebill_id(payment_status_response["OrderId"], payment_id)
                            if rebill_id:
                                subscription_end_date = datetime.now() + timedelta(days=30)  # Пример, подписка на 30 дней
                                update_user_subscription(db, user_id, subscription_status="ACTIVE", subscription_type=subscription_type, subscription_end_date=subscription_end_date, rebill_id=rebill_id)
                                await callback_query.message.answer("Оплата успешно подтверждена и подписка активирована.")
                                return
                            else:
                                await callback_query.message.answer("Ошибка при получении RebillId, обратитесь в поддержку.")
                                return
                        elif payment_status_response["Status"] in ["CANCELED", "REJECTED"]:
                            await callback_query.message.answer("Операция отменена.")
                            return
                    else:
                        await callback_query.message.answer("Ошибка при проверке статуса платежа, обратитесь в поддержку.")
                        return
                except Exception as e:
                    print(f"Error in payment status check: {e}")
                    await callback_query.message.answer("Ошибка при проверке статуса платежа, обратитесь в поддержку.")
                    return
                await asyncio.sleep(10)  # Ждем 10 секунд перед следующей проверкой
            await callback_query.message.answer("Вы не оплатили подписку в течение 5 минут. Пожалуйста, попробуйте снова.")
    except Exception as e:
        print(f"Error in check_payment_status_and_update_db: {e}")

@tinkoff_router.callback_query(F.data == "check999")
async def check999_subscribe(callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        order_id = f"{user_id}_{int(time.time())}"
        amount = 99900  # Сумма в копейках (999 рублей)

        async with SessionManager() as db:
            user_info = get_user_info(db=db, user_id=user_id)
            if not user_info or not user_info.customer_key:
                await callback_query.message.answer("Ошибка при получении данных пользователя, обратитесь в поддержку.")
                return
            customer_key = user_info.customer_key

        description = "Проверка: 999р в мес"
        payment_response = await tinkoff_api.init_payment(amount, order_id, description, customer_key)
        if payment_response["Success"]:
            payment_id = payment_response["PaymentId"]
            payment_url = payment_response["PaymentURL"]

            # Создаем inline кнопку с URL
            women_subscribe = [
                [InlineKeyboardButton(text="Оплатить 999р", url=payment_url)]
            ]
            sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)

            await callback_query.message.answer("Для оплаты нажмите на кнопку ниже:", reply_markup=sub_inline)
            await asyncio.create_task(check_payment_status_and_update_db(callback_query, payment_id, user_id, "Проверка"))
        else:
            await callback_query.message.answer("Произошла ошибка при инициализации платежа, обратитесь в поддержку.")
    except Exception as e:
        print(f"Error in check999_subscribe: {e}")
        await callback_query.message.answer("Произошла ошибка, обратитесь в поддержку.")

@tinkoff_router.callback_query(F.data == "questionnaire1500")
async def questionnaire1500_subscribe(callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        order_id = f"{user_id}_{int(time.time())}"
        amount = 150000  # Сумма в копейках (1500 рублей)

        async with SessionManager() as db:
            user_info = get_user_info(db=db, user_id=user_id)
            if not user_info or not user_info.customer_key:
                await callback_query.message.answer("Ошибка при получении данных пользователя, обратитесь в поддержку.")
                return
            customer_key = user_info.customer_key

        description = "Анкета: 1500р в мес"
        payment_response = await tinkoff_api.init_payment(amount, order_id, description, customer_key)

        if payment_response["Success"]:
            payment_id = payment_response["PaymentId"]
            payment_url = payment_response["PaymentURL"]

            # Создаем inline кнопку с URL
            women_subscribe = [
                [InlineKeyboardButton(text="Оплатить 1500р", url=payment_url)]
            ]
            sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)

            await callback_query.message.answer("Для оплаты нажмите на кнопку ниже:", reply_markup=sub_inline)
            await asyncio.create_task(check_payment_status_and_update_db(callback_query, payment_id, user_id, "Анкета"))
        else:
            await callback_query.message.answer("Произошла ошибка при инициализации платежа, обратитесь в поддержку.")
    except Exception as e:
        print(f"Error in questionnaire1500_subscribe: {e}")
        await callback_query.message.answer("Произошла ошибка, обратитесь в поддержку.")

@tinkoff_router.callback_query(F.data == "check_and_questionnaire")
async def check_and_questionnaire_subscribe(callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        order_id = f"{user_id}_{int(time.time())}"
        amount = 99900  # Сумма в копейках (999 рублей)

        async with SessionManager() as db:
            user_info = get_user_info(db=db, user_id=user_id)
            if not user_info or not user_info.customer_key:
                await callback_query.message.answer("Ошибка при получении данных пользователя, обратитесь в поддержку.")
                return
            customer_key = user_info.customer_key

        description = "Акция! Проверка + Анкета: 999р"
        payment_response = await tinkoff_api.init_payment(amount, order_id, description, customer_key)
        if payment_response["Success"]:
            payment_id = payment_response["PaymentId"]
            payment_url = payment_response["PaymentURL"]

            # Создаем inline кнопку с URL
            women_subscribe = [
                [InlineKeyboardButton(text="Оплатить 999р", url=payment_url)]
            ]
            sub_inline = InlineKeyboardMarkup(inline_keyboard=women_subscribe)

            await callback_query.message.answer("Для оплаты нажмите на кнопку ниже:", reply_markup=sub_inline)
            await asyncio.create_task(check_payment_status_and_update_db(callback_query, payment_id, user_id, "Проверка + Анкета"))
        else:
            await callback_query.message.answer("Произошла ошибка при инициализации платежа, обратитесь в поддержку.")
    except Exception as e:
        print(f"Error in check_and_questionnaire_subscribe: {e}")
        await callback_query.message.answer("Произошла ошибка, обратитесь в поддержку.")

# async def recurring_payment():
#     while True:
#         try:
#             async with SessionManager() as db:
#                 users = db.query(User).filter(
#                     User.subscription_status == "ACTIVE",
#                     User.subscription_end_date <= datetime.now()
#                 ).all()
#
#                 for user in users:
#                     try:
#                         order_id = f"{user.user_id}_{int(time.time())}"
#                         amount = 99900 if user.subscription_type == "Проверка" else 150000  # Пример для разных типов подписок
#
#                         payment_response = await tinkoff_api.init_payment(amount, order_id, f"Рекуррентный платеж: {user.subscription_type}", user.customer_key)
#                         if payment_response["Success"]:
#                             payment_id = payment_response["PaymentId"]
#                             charge_response = await tinkoff_api.charge_payment(payment_id, user.rebill_id)
#
#                             if charge_response["Success"]:
#                                 subscription_end_date = datetime.now() + timedelta(days=30)  # Обновляем дату окончания подписки
#                                 update_user_subscription(db, user.user_id, "ACTIVE", user.subscription_type, subscription_end_date, user.rebill_id)
#                             else:
#                                 update_user_subscription(db, user.user_id, "INACTIVE", user.subscription_type, None, user.rebill_id)
#                                 # Уведомляем пользователя о необходимости продления подписки вручную или другой проблеме
#                         else:
#                             update_user_subscription(db, user.user_id, "INACTIVE", user.subscription_type, None, user.rebill_id)
#                             # Уведомляем пользователя о необходимости продления подписки вручную или другой проблеме
#                     except Exception as e:
#                         print(f"Error processing user {user.user_id}: {e}")
#                         update_user_subscription(db, user.user_id, "INACTIVE", user.subscription_type, None, user.rebill_id)
#                         # Уведомляем пользователя о необходимости продления подписки вручную или другой проблеме
#             await asyncio.sleep(60)  # Проверяем каждые 60 секунд для тестирования
#         except Exception as e:
#             print(f"Error in recurring_payment: {e}")
#
# # Запускаем фоновую задачу
# loop = asyncio.get_event_loop()
# loop.create_task(recurring_payment())
# loop.run_forever()
