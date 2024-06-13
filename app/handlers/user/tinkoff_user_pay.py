import asyncio
import hashlib
import time
from datetime import datetime, timedelta

import aiohttp
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from app.database.models.users import User, async_session_maker
from app.database.requests.crud import get_user_info, update_user_subscription

tinkoff_router = Router()


class SessionManager:
    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = async_session_maker()
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()


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
            print(f"Ошибка в init_payment: {e}")
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
            print(f"Ошибка в get_payment_status: {e}")
            return {"Success": False, "Message": "Ошибка соединения с сервером оплаты"}

    async def charge_payment(self, payment_id, rebill_id):
        print("Запуск charge_payment")
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
                    response_json = await response.json()
                    print(f"Результат charge_payment: {response_json}")
                    return response_json
        except aiohttp.ClientError as e:
            print(f"Ошибка в charge_payment: {e}")
            return {"Success": False, "Message": "Ошибка соединения с сервером оплаты"}

    async def cancel_payment(self, payment_id):
        print("Запуск cancel_payment")
        url = self.BASE_URL + "Cancel"
        params = {
            "PaymentId": payment_id,
            "TerminalKey": self.terminal_key,
        }
        ordered_keys = ['PaymentId', 'TerminalKey']
        params["Token"] = self.generate_token(params, ordered_keys)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params, ssl=False) as response:
                    response_json = await response.json()
                    print(f"Результат cancel_payment: {response_json}")
                    return response_json
        except aiohttp.ClientError as e:
            print(f"Ошибка в cancel_payment: {e}")
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
        print(f"Ошибка в get_rebill_id: {e}")
        return None


async def check_payment_status_and_update_db(callback_query: CallbackQuery,
                                             payment_id,
                                             user_id,
                                             subscription_type):
    print("Запуск check_payment_status_and_update_db")
    try:
        async with SessionManager() as db:
            user_info = await get_user_info(db=db,
                                            user_id=user_id)
            if not user_info:
                await callback_query.message.answer("Не удалось найти информацию о пользователе.")
                return

            for _ in range(30):
                try:
                    payment_status_response = await tinkoff_api.get_payment_status(payment_id)
                    if payment_status_response["Success"]:
                        if payment_status_response["Status"] == "CONFIRMED":
                            await asyncio.sleep(5)
                            rebill_id = await get_rebill_id(payment_status_response["OrderId"], payment_id)
                            if rebill_id:
                                subscription_end_date = datetime.now() + timedelta(days=30)
                                async with SessionManager() as update_db:
                                    await update_user_subscription(update_db,
                                                                   user_id,
                                                                   subscription_status="ACTIVE",
                                                                   subscription_type=subscription_type,
                                                                   subscription_end_date=subscription_end_date,
                                                                   rebill_id=rebill_id, payment_id=payment_id)
                                await callback_query.message.answer(
                                    "Оплата успешно подтверждена и подписка активирована.")
                                print(f"Подписка активирована для пользователя {user_id}")
                                return
                            else:
                                await callback_query.message.answer(
                                    "Ошибка! Обратитесь в поддержку или попробуйте снова.")
                                return
                        elif payment_status_response["Status"] in ["CANCELED", "REJECTED"]:
                            await callback_query.message.answer("Операция отменена.")
                            return
                    else:
                        await callback_query.message.answer(
                            "Ошибка, обратитесь в поддержку или попробуйте снова.")
                        return
                except Exception as e:
                    print(f"Ошибка в check_payment_status_and_update_db при проверке статуса: {e}")
                    await callback_query.message.answer("Ошибка при проверке статуса платежа, обратитесь в поддержку.")
                    return
                await asyncio.sleep(10)
            await callback_query.message.answer(
                "Вы не оплатили подписку в течение 30 дней. Пожалуйста, попробуйте снова.")
    except Exception as e:
        print(f"Ошибка в check_payment_status_and_update_db: {e}")


async def confirm_subscribe(callback_query: CallbackQuery, subscription_type: str):
    try:
        await callback_query.message.answer(
            "Даю согласие на "
            "<a href='https://telegra.ph/Soglasie-na-obrabotku-personalnyh-dannyh-06-12'>Обработку персональных данных</a> и "
            "<a href='https://telegra.ph/Soglasie-na-sohranenie-uchetnyh-dанных-для-будущих-транзакций-06-12'>Согласие на сохранение учетных данных для будущих транзакций</a>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Да", callback_data=f"user_agree_{subscription_type}")],
                [InlineKeyboardButton(text="Нет", callback_data="user_disagree")]
            ])
        )
    except Exception as e:
        print(e)


@tinkoff_router.callback_query(F.data.startswith("user_agree_"))
async def user_agree(callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        subscription_type = callback_query.data.split("_")[2]  # Получаем тип подписки из callback_data

        async with SessionManager() as db:
            user_info = await get_user_info(db=db, user_id=user_id)
            if not user_info or not user_info.customer_key:
                await callback_query.message.answer(
                    "Ошибка при получении данных пользователя, обратитесь в поддержку.")
                return

        if subscription_type == "Проверка":
            amount = 99900
        elif subscription_type == "Анкета":
            amount = 150000
        elif subscription_type == "Проверка + Анкета":
            amount = 99900
        else:
            await callback_query.message.answer("Неизвестный тип подписки, обратитесь в поддержку.")
            return

        description = subscription_type

        await callback_query.message.answer(
            f"<b>Соглашение с подпиской:</b>\n\n"
            f"<b>Сумма сделки:</b> {amount / 100:.2f}р/мес\n\n"
            f"<b>Тип подписки:</b> {subscription_type}\n\n"
            "<b>Тип валюты:</b> рубли\n\n"
            "<b>Правила отмены и возврата:</b> за 24 часа вы можете отменить подписку, также вернуть деньги при неиспользовании купленного функционала бота в соответствии с подпиской\n\n\n"
            "<b>Контакт:</b> @esc222",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Согласен, оплатить", callback_data=f"proceed_payment_{subscription_type}")],
                [InlineKeyboardButton(text="Отказаться", callback_data="user_decline")]
            ])
        )
    except Exception as e:
        print(e)


@tinkoff_router.callback_query(F.data.startswith("proceed_payment_"))
async def proceed_payment(callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        subscription_type = callback_query.data.split("_")[2]  # Получаем тип подписки из callback_data
        order_id = f"{user_id}_{int(time.time())}"

        async with SessionManager() as db:
            user_info = await get_user_info(db=db, user_id=user_id)
            if not user_info or not user_info.customer_key:
                await callback_query.message.answer("Ошибка при получении данных пользователя, обратитесь в поддержку.")
                return
            customer_key = user_info.customer_key

        if subscription_type == "Проверка":
            amount = 99900  # 999 рублей в копейках
            description = "Проверка"
        elif subscription_type == "Анкета":
            amount = 150000  # 1500 рублей в копейках
            description = "Анкета"
        elif subscription_type == "Проверка + Анкета":
            amount = 249900  # 2499 рублей в копейках
            description = "Проверка + Анкета"
        else:
            await callback_query.message.answer("Неизвестный тип подписки, обратитесь в поддержку.")
            return

        payment_response = await tinkoff_api.init_payment(amount, order_id, description, customer_key)
        if payment_response["Success"]:
            payment_id = payment_response["PaymentId"]
            payment_url = payment_response["PaymentURL"]

            # Создаем inline кнопку с URL
            payment_button = [
                [InlineKeyboardButton(text="Оплатить", url=payment_url)]
            ]
            sub_inline = InlineKeyboardMarkup(inline_keyboard=payment_button)

            await callback_query.message.answer("Для оплаты нажмите на кнопку ниже:", reply_markup=sub_inline)
            await asyncio.create_task(check_payment_status_and_update_db(callback_query, payment_id, user_id, subscription_type))
        else:
            await callback_query.message.answer("Произошла ошибка при инициализации платежа, обратитесь в поддержку.")
    except Exception as e:
        print(e)


@tinkoff_router.callback_query(F.data == "user_disagree")
async def user_disagree(callback_query: CallbackQuery):
    await callback_query.message.answer("Без согласия мы не можем оформить подписку по требованиям банка.")


@tinkoff_router.callback_query(F.data == "user_decline")
async def user_decline(callback_query: CallbackQuery):
    await callback_query.message.answer("Вы отказались от подписки.")


@tinkoff_router.callback_query(F.data == "check999")
async def check999_subscribe(callback_query: CallbackQuery):
    print("Запуск check999_subscribe")
    user_id = callback_query.from_user.id
    await confirm_subscribe(callback_query, "Проверка")


@tinkoff_router.callback_query(F.data == "questionnaire1500")
async def questionnaire1500_subscribe(callback_query: CallbackQuery):
    print("Запуск questionnaire1500_subscribe")
    user_id = callback_query.from_user.id
    await confirm_subscribe(callback_query, "Анкета")


@tinkoff_router.callback_query(F.data == "check_and_questionnaire")
async def check_and_questionnaire_subscribe(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await confirm_subscribe(callback_query, "Проверка + Анкета")


async def check_subscriptions():
    try:
        async with SessionManager() as db:
            result = await db.execute(select(User).filter(User.subscription_status == "ACTIVE"))
            users = result.scalars().all()
            now = datetime.now().replace(microsecond=0)
            print(f"Текущее время: {now}")

            for user in users:
                subscription_end_datetime = user.subscription_end_date

                print(f"Время окончания подписки для пользователя {user.user_id}: {subscription_end_datetime}")

                if subscription_end_datetime <= now:
                    print(f"Подписка истекла для пользователя {user.user_id}")
                    await renew_subscription(user)
                else:
                    print(f"Подписка активна для пользователя {user.user_id}")
    except Exception as e:
        print(f"Ошибка в check_subscriptions: {e}")


async def renew_subscription(user):
    print(f"Запуск renew_subscription для пользователя {user.user_id}")
    try:
        order_id = f"{user.user_id}_{int(time.time())}"

        if user.subscription_type == "Проверка":
            amount = 99900  # 999 рублей в копейках
            description = "Продление подписки: Проверка"
        elif user.subscription_type == "Анкета":
            amount = 150000  # 1500 рублей в копейках
            description = "Продление подписки: Анкета"
        elif user.subscription_type == "Проверка + Анкета":
            amount = 249900  # 2499 рублей в копейках
            description = "Продление подписки: Проверка + Анкета"
        else:
            print(f"Неизвестный тип подписки для пользователя {user.user_id}")
            return

        payment_response = await tinkoff_api.init_payment(amount, order_id, description, user.customer_key)
        print(f"Инициация платежа: {payment_response}")
        if payment_response["Success"]:
            payment_id = payment_response["PaymentId"]

            charge_response = await tinkoff_api.charge_payment(payment_id, user.rebill_id)
            print(f"Результат рекуррентного платежа: {charge_response}")
            if charge_response["Success"] and charge_response["Status"] == "CONFIRMED":
                async with SessionManager() as db:
                    user_info = await get_user_info(db=db, user_id=user.user_id)
                    print(f"Информация о пользователе: {user_info}")

                if user_info:
                    async with SessionManager() as db:
                        subscription_end_date = (datetime.now() + timedelta(days=30)).replace(
                            microsecond=0)
                        await update_user_subscription(
                            db, user.user_id,
                            subscription_status="ACTIVE",
                            subscription_type=user.subscription_type,
                            subscription_end_date=subscription_end_date,
                            rebill_id=user.rebill_id,
                            payment_id=payment_id
                        )
                        print(f"Подписка пользователя {user.user_id} успешно продлена до {subscription_end_date}.")
                else:
                    print(f"Не удалось найти информацию о пользователе {user.user_id}.")
            else:
                print(
                    f"Ошибка при выполнении рекуррентного платежа для пользователя {user.user_id}: {charge_response['Message']}")
        else:
            print(f"Ошибка при инициализации платежа для пользователя {user.user_id}: {payment_response['Message']}")
    except Exception as e:
        print(f"Ошибка в renew_subscription для пользователя {user.user_id}: {e}")
