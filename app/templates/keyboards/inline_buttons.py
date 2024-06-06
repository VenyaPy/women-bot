from aiogram.types import InlineKeyboardButton


gender_start = [
    [
        InlineKeyboardButton(text="Мужской", callback_data="man_gender"),
        InlineKeyboardButton(text="Женский", callback_data="woman_gender")
    ]
]


city_choose = [
    [InlineKeyboardButton(text="Москва", callback_data="city_moscow")],
    [InlineKeyboardButton(text="Санкт-Петербург", callback_data="city_saint_petersburg")],
    [InlineKeyboardButton(text="Новосибирск", callback_data="city_novosibirsk")],
    [InlineKeyboardButton(text="Екатеринбург", callback_data="city_yekaterinburg")],
    [InlineKeyboardButton(text="Казань", callback_data="city_kazan")],
    [InlineKeyboardButton(text="Нижний Новгород", callback_data="city_nizhny_novgorod")],
    [InlineKeyboardButton(text="Челябинск", callback_data="city_chelyabinsk")],
    [InlineKeyboardButton(text="Красноярск", callback_data="city_krasnoyarsk")],
    [InlineKeyboardButton(text="Самара", callback_data="city_samara")],
    [InlineKeyboardButton(text="Ростов на Дону", callback_data="city_rostov_on_don")],
    [InlineKeyboardButton(text="Омск", callback_data="city_omsk")],
    [InlineKeyboardButton(text="Краснодар", callback_data="city_krasnodar")],
    [InlineKeyboardButton(text="Воронеж", callback_data="city_voronezh")],
    [InlineKeyboardButton(text="Волгоград", callback_data="city_volgograd")],
    [InlineKeyboardButton(text="Пермь", callback_data="city_perm")]
]