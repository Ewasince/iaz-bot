from aiogram.fsm.state import State, StatesGroup


class States(StatesGroup):
    """
    Перечисление всех состояних бота
    """

    default_state = State()
    start_queue = State()
