import hashlib

def generate_token(params, password):
    # Добавляем пароль в параметры
    params_with_password = params.copy()
    params_with_password['Password'] = password

    # Отсортируем параметры по ключу в алфавитном порядке
    sorted_params = sorted((key, value) for key, value in params_with_password.items() if key != 'DATA')

    # Конкатенируем только значения пар в одну строку
    token_str = ''.join(str(value) for key, value in sorted_params)

    # Применяем хеш-функцию SHA-256
    token = hashlib.sha256(token_str.encode('utf-8')).hexdigest()

    # Возвращаем токен в нижнем регистре
    return token.lower()

params = {
    "TerminalKey": "1717831041748DEMO",
    "Amount": "99900",
    "OrderId": "12345_1650984321",
    "Description": "Проверка: 999р в мес",
    "DATA": {
        "CustomerKey": "customer_123"
    }
}

password = "C^P0Gczux%x7otV#"

# Генерируем токен
token = generate_token(params, password)

print(token)