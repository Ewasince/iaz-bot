from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.main_menu import main_markup
from keyboards.student import student_card, mark_card
from queue_maker import SheetWrapper
from enums import Mark

router = Router()
SAMPLE_SPREADSHEET_ID = "120kLLJRpbZjQofJuPbbB-VtvebMQzG6GLBV24FZGO58"


@router.callback_query(F.data == 'next_student')
async def process_callback_next_student(callback_query: CallbackQuery, state: FSMContext):
    s = SheetWrapper(SAMPLE_SPREADSHEET_ID)

    state_date = await state.get_data()

    await state.update_data(id=state_date['id'] + 1)

    curr_student = s.get_next_student(state_date['id'] + 1)

    if curr_student is None:
        await state.clear()
        await callback_query.message.edit_text(
            text='Очередь закончилась',
            reply_markup=main_markup,
        )
        return

    await callback_query.message.edit_text(
        text=f"""
Студент: {curr_student[0]}
Группа: {curr_student[2]}
№ Темы {curr_student[1]}
    """,
        reply_markup=student_card
    )


@router.callback_query(F.data == 'previous_student')
async def process_callback_previous_student(callback_query: CallbackQuery, state: FSMContext):
    s = SheetWrapper(SAMPLE_SPREADSHEET_ID)

    state_date = await state.get_data()

    if state_date['id'] >= 1:
        await state.update_data(id=state_date['id'] - 1)
        curr_student = s.get_next_student(state_date['id'] - 1)

        if curr_student is None:
            await callback_query.message.edit_text(
                text='Очередь закончилась',
                reply_markup=main_markup,
            )

        await callback_query.message.edit_text(
            text=f"""
Студент: {curr_student[0]}
Группа: {curr_student[2]}
№ Темы {curr_student[1]}
            """,
            reply_markup=student_card
        )


@router.callback_query(F.data == 'set_mark')
async def process_callback_previous_student(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(
        text='Какую оценку поставить',
        reply_markup=mark_card
    )


@router.callback_query(F.data == 'set_mark_success')
async def process_callback_set_mark_success(callback_query: CallbackQuery, state: FSMContext):
    s = SheetWrapper(SAMPLE_SPREADSHEET_ID)

    state_date = await state.get_data()
    curr_student = s.get_next_student(state_date['id'])

    s.increment_queue(state_date['id'])
    s.mark_current_student(Mark.good, comment='Сдал')

    await callback_query.message.edit_text(
        text=f"""Студент оценен
Студент: {curr_student[0]}
Группа: {curr_student[2]}
№ Темы {curr_student[1]}
        """,
        reply_markup=student_card
    )


@router.callback_query(F.data == 'set_mark_failed')
async def process_callback_set_mark_failed(callback_query: CallbackQuery, state: FSMContext):
    s = SheetWrapper(SAMPLE_SPREADSHEET_ID)

    state_date = await state.get_data()
    curr_student = s.get_next_student(state_date['id'])

    s.increment_queue(state_date['id'])
    s.mark_current_student(Mark.bad, comment='Не Сдал)')

    await callback_query.message.edit_text(
        text=f"""Студент оценен
    Студент: {curr_student[0]}
    Группа: {curr_student[2]}
    № Темы {curr_student[1]}
            """,
        reply_markup=student_card
    )
