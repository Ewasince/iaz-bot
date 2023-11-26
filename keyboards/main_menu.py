from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Кнопка начала просмотра очереди
inline_btn_start_queue = InlineKeyboardButton(
    text="Начать защиту работ",
    callback_data="start_queue",
)

# Кнопка инициализации очереди
inline_btn_init_queue = InlineKeyboardButton(
    text="Собрать очередь",
    callback_data="init_queue",
)


# Главное меню
main_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [inline_btn_start_queue],
        [inline_btn_init_queue],
    ]
)
