from aiogram.fsm.state import State, StatesGroup


class AddProductStates(StatesGroup):
    enter_name = State()
    enter_description = State()
    enter_price = State()
    select_category = State()


class AddCategoryStates(StatesGroup):
    enter_name = State()
