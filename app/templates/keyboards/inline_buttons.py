from aiogram.types import InlineKeyboardButton


gender_start = [
    [
        InlineKeyboardButton(text="Мужской", callback_data="man_gender"),
        InlineKeyboardButton(text="Женский", callback_data="woman_gender")
    ]
]

read_faq_inline = [
    [
        InlineKeyboardButton(text="Прочитать инструкцию", callback_data="faq_reader")
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


women_subscribe = [
    [
        InlineKeyboardButton(text="Проверка: 999р/мес", callback_data="subscribe_999_check")
    ],
    [
        InlineKeyboardButton(text="Анкета: 1500р/мес", callback_data="subscribe_1500_questionnaire")
    ],
    [
        InlineKeyboardButton(text="Акция! Проверка + Анкета: 999р/мес", callback_data="subscribe_999_check_and_questionnaire")
    ]
]

is_cancel_sub = [
    [
        InlineKeyboardButton(text="Да", callback_data="yes_cancel_button"),
        InlineKeyboardButton(text="Нет", callback_data="no_cancel_button"),

    ]
]

subscribe = [
    [
        InlineKeyboardButton(text="Проверка: 999р в мес", url="")
    ]
]

politic_buttons = [
    [
        InlineKeyboardButton(text="Оферта",
                             url="https://telegra.ph/Oferta-06-12-2")
    ],
    [
        InlineKeyboardButton(text="Политика конфиденциальности",
                             url="https://telegra.ph/Politika-konfidencialnosti-06-12-11")
    ]
]

positive_or_negative = [
    [
        InlineKeyboardButton(text="Положительный", callback_data="review_positive")
    ],
    [
        InlineKeyboardButton(text="Отрицательный", callback_data="review_negative")
    ]
]


add_or_not_add_review = [
    [
        InlineKeyboardButton(text="Добавить отзыв", callback_data="want_to_add_review")
    ],
    [
        InlineKeyboardButton(text="Не хочу добавлять", callback_data="dont_want_to_add")
    ]
]


send_or_delete_review = [
    [
        InlineKeyboardButton(text="Отправить", callback_data="send_review_to_bd")
    ],
    [
        InlineKeyboardButton(text="Отменить", callback_data="cancel_review")
    ]
]


other_city = [
    [
        InlineKeyboardButton(text="Обновить", callback_data="update_profile_list"),
        InlineKeyboardButton(text="Изменить город", callback_data="other_city_callback")
    ]
]

girl_profile_choose = [
    [
        InlineKeyboardButton(text="Удалить анкету", callback_data="del_my_profile")
    ]
]


enough_photo_women = [
    [
        InlineKeyboardButton(text="Добавить анкету", callback_data="enough_photos"),
        InlineKeyboardButton(text="Отменить", callback_data="cancel_send_profile")
    ]
]


is_check_post = [
    [
        InlineKeyboardButton(text="Посмотреть результат", callback_data="check_mailing_result")
    ]
]


send_or_delete_mail = [
    [
        InlineKeyboardButton(text="Отправить пост", callback_data="send_mail"),
        InlineKeyboardButton(text="Удалить пост", callback_data="delete_mail")
    ]
]


users_of_mailing = [
    [
        InlineKeyboardButton(text="Всем", callback_data="send_to_all")
    ],
    [
        InlineKeyboardButton(text="Мужчинам", callback_data="send_mail_to_mens")
    ],
    [
        InlineKeyboardButton(text="Неоформленным подпискам", callback_data="send_mail_to_women")
    ],
    [
        InlineKeyboardButton(text="Оформленным подпискам", callback_data="send_mail_to_subscribers")
    ],
]