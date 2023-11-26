from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Кнопка след студент
inline_btn_next_student = InlineKeyboardButton(
    text="Следующий студент",
    callback_data="next_student",
)

# Кнопка предыдущий студент
inline_btn_previous_student = InlineKeyboardButton(
    text="Предыдущий студент",
    callback_data="previous_student",
)

# Кнопка Поставить оценку
inline_btn_set_mark = InlineKeyboardButton(
    text="Поставить оценку",
    callback_data="set_mark",
)

# Карточка студента
student_card = InlineKeyboardMarkup(
    inline_keyboard=[
        [inline_btn_previous_student, inline_btn_next_student],
        [inline_btn_set_mark],
    ]
)

inline_btn_set_mark_success = InlineKeyboardButton(
    text="Защитил",
    callback_data="set_mark_success",
)

inline_btn_set_mark_failed = InlineKeyboardButton(
    text="Не Защитил",
    callback_data="set_mark_failed",
)

# Оценивание студента
mark_card = InlineKeyboardMarkup(
    inline_keyboard=[[inline_btn_set_mark_success, inline_btn_set_mark_failed]]
)
