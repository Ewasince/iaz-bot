from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from errors import EmptyList
from keyboards.main_menu import main_markup
from keyboards.student import student_card
from queue_maker import SheetWrapper, SAMPLE_SPREADSHEET_ID

router = Router()

@router.message(Command(commands=["start"]))
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        text="Привет, я бот, который помогает управлять очередью сдачи дополнительных проектов",
        reply_markup=main_markup,
    )


@router.callback_query(F.data == "init_queue")
async def process_callback_init_queue(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(text="Начался сбор очереди на сдачу")
    s = SheetWrapper(SAMPLE_SPREADSHEET_ID)

    lists_with_students = s.get_students_sheets()
    print(f"Список групп: {lists_with_students}")

    groups_list = []

    for l in lists_with_students:
        try:
            st_list = s.get_students_from_list(l)

        except EmptyList as e:
            print(e)
            continue

        groups_list.append(st_list)

    queue = s.shuffle_students(groups_list)
    s.write_queue(queue)

    await callback_query.message.edit_text(
        text="Очередь сгенерирована",
        reply_markup=main_markup,
    )


@router.callback_query(F.data == "start_queue")
async def process_callback_start_queue(
    callback_query: CallbackQuery, state: FSMContext
):
    s = SheetWrapper(SAMPLE_SPREADSHEET_ID)

    student_id = 0

    if state_data := await state.get_data():
        student_id = state_data["id"]
    else:
        await state.update_data(id=student_id)

    curr_student = s.get_next_student(student_id)

    if curr_student is None:
        await callback_query.message.edit_text(
            text="Очередь закончилась",
            reply_markup=main_markup,
        )

    await callback_query.message.edit_text(
        text=f"""
Студент: {curr_student[0]}
Группа: {curr_student[2]}
№ Темы {curr_student[1]}
""",
        reply_markup=student_card,
    )
